#!/usr/bin/env python3
"""
Hardware Pipeline - Real Playwright Component Scraper
Scrapes DigiKey and Mouser for component data
Saves to PostgreSQL cache
"""

import asyncio
import json
import re
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import hashlib

from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
import psycopg2
from psycopg2.extras import Json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles PostgreSQL database operations"""
    
    def __init__(self, host='postgres', port=5432, database='hardware_pipeline', 
                 user='postgres', password='hardwarepipeline2026'):
        self.conn_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            logger.info("✅ Database connected")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database disconnected")
    
    def check_cache(self, search_term: str, category: str) -> Optional[List[Dict]]:
        """Check if components are in cache and not expired"""
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT 
                    part_number, manufacturer, description, category,
                    datasheet_url, specifications, pricing, availability,
                    lifecycle_status, source, cached_at
                FROM component_cache
                WHERE search_term ILIKE %s
                    AND category = %s
                    AND expires_at > NOW()
                    AND lifecycle_status IN ('Active', 'NRND')
                ORDER BY 
                    CASE lifecycle_status 
                        WHEN 'Active' THEN 1
                        WHEN 'NRND' THEN 2
                        ELSE 3
                    END,
                    cached_at DESC
                LIMIT 10
            """
            cursor.execute(query, (f'%{search_term}%', category))
            rows = cursor.fetchall()
            cursor.close()
            
            if rows:
                logger.info(f"✅ Cache HIT: Found {len(rows)} components for '{search_term}'")
                return [
                    {
                        'part_number': row[0],
                        'manufacturer': row[1],
                        'description': row[2],
                        'category': row[3],
                        'datasheet_url': row[4],
                        'specifications': row[5],
                        'pricing': row[6],
                        'availability': row[7],
                        'lifecycle_status': row[8],
                        'source': row[9],
                        'cached_at': row[10].isoformat()
                    }
                    for row in rows
                ]
            else:
                logger.info(f"❌ Cache MISS: No cached components for '{search_term}'")
                return None
                
        except Exception as e:
            logger.error(f"Cache check error: {e}")
            return None
    
    def save_component(self, component: Dict, search_term: str, category: str):
        """Save component to cache"""
        try:
            cursor = self.conn.cursor()
            
            # Calculate expiry (30 days from now)
            expires_at = datetime.now() + timedelta(days=30)
            
            query = """
                INSERT INTO component_cache (
                    part_number, manufacturer, description, category,
                    datasheet_url, specifications, pricing, availability,
                    lifecycle_status, source, search_term, cached_at, expires_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                ON CONFLICT (part_number) DO UPDATE SET
                    description = EXCLUDED.description,
                    pricing = EXCLUDED.pricing,
                    availability = EXCLUDED.availability,
                    cached_at = NOW(),
                    expires_at = EXCLUDED.expires_at,
                    search_term = EXCLUDED.search_term
            """
            
            cursor.execute(query, (
                component['part_number'],
                component['manufacturer'],
                component['description'],
                category,
                component.get('datasheet_url', ''),
                Json(component.get('specifications', {})),
                Json(component.get('pricing', {})),
                Json(component.get('availability', {})),
                component.get('lifecycle_status', 'Active'),
                component['source'],
                search_term,
                expires_at
            ))
            
            self.conn.commit()
            cursor.close()
            logger.debug(f"Saved: {component['part_number']}")
            
        except Exception as e:
            logger.error(f"Error saving component {component.get('part_number', 'unknown')}: {e}")
            self.conn.rollback()


class DigiKeyScraper:
    """Scrapes DigiKey for component data"""
    
    def __init__(self, browser: Browser):
        self.browser = browser
        self.base_url = 'https://www.digikey.com'
    
    async def scrape(self, search_term: str, category: str) -> List[Dict]:
        """Scrape DigiKey for components"""
        logger.info(f"🔍 DigiKey: Searching for '{search_term}'")
        
        page = await self.browser.new_page()
        results = []
        
        try:
            # Navigate to DigiKey
            await page.goto(self.base_url, timeout=30000, wait_until='domcontentloaded')
            logger.debug("DigiKey homepage loaded")
            
            # Handle cookie consent if present
            try:
                cookie_button = page.locator('button:has-text("Accept All Cookies")')
                if await cookie_button.is_visible(timeout=2000):
                    await cookie_button.click()
                    logger.debug("Accepted cookies")
            except:
                pass
            
            # Search
            search_selectors = [
                'input[id="searchInput"]',
                'input[name="keywords"]',
                'input[placeholder*="Search"]',
                '#search-input',
                '.search-input'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = page.locator(selector).first
                    if await search_input.is_visible(timeout=2000):
                        break
                except:
                    continue
            
            if not search_input:
                logger.warning("⚠️ DigiKey: Could not find search input")
                return results
            
            await search_input.fill(search_term)
            await search_input.press('Enter')
            logger.debug("Search submitted")
            
            # Wait for results
            try:
                await page.wait_for_selector('table.product-table, .product-list, [data-testid="product-table"]', timeout=15000)
                logger.debug("Results loaded")
            except PlaywrightTimeout:
                logger.warning("⚠️ DigiKey: Timeout waiting for results")
                return results
            
            # Extract product rows
            product_selectors = [
                'tr[itemtype*="Product"]',
                'tr.product-row',
                '[data-testid="product-row"]',
                'table.product-table tbody tr'
            ]
            
            products = []
            for selector in product_selectors:
                products = await page.locator(selector).all()
                if products:
                    break
            
            logger.info(f"Found {len(products)} product rows")
            
            # Process each product (limit to top 5)
            for i, product_row in enumerate(products[:5]):
                try:
                    component = await self._extract_digikey_product(product_row, category)
                    if component and component['part_number']:
                        results.append(component)
                        logger.debug(f"Extracted: {component['part_number']}")
                except Exception as e:
                    logger.warning(f"Failed to extract product {i+1}: {e}")
                    continue
            
            logger.info(f"✅ DigiKey: Extracted {len(results)} components")
            
        except Exception as e:
            logger.error(f"❌ DigiKey scraping error: {e}")
        
        finally:
            await page.close()
        
        return results
    
    async def _extract_digikey_product(self, row, category: str) -> Optional[Dict]:
        """Extract product details from a DigiKey row"""
        try:
            # Part number
            part_selectors = [
                '[data-testid="product-mfr-part-number"]',
                '.product-mfr-part-number',
                '[itemprop="productID"]',
                'td:has-text("Part Number")'
            ]
            part_number = await self._get_text(row, part_selectors)
            
            # Manufacturer
            mfg_selectors = [
                '[data-testid="product-manufacturer"]',
                '.manufacturer',
                '[itemprop="manufacturer"]'
            ]
            manufacturer = await self._get_text(row, mfg_selectors)
            
            # Description
            desc_selectors = [
                '[data-testid="product-description"]',
                '.product-description',
                '[itemprop="description"]'
            ]
            description = await self._get_text(row, desc_selectors)
            
            # Price
            price_selectors = [
                '[data-testid="price-unit"]',
                '.price-unit',
                '[itemprop="price"]',
                '.product-dollars'
            ]
            price = await self._get_text(row, price_selectors)
            
            # Stock/Availability
            stock_selectors = [
                '[data-testid="product-quantity"]',
                '.product-stock',
                '.availability'
            ]
            stock = await self._get_text(row, stock_selectors)
            
            # Datasheet link
            datasheet_url = ''
            try:
                datasheet_link = row.locator('a:has-text("Datasheet"), a:has-text("PDF")').first
                datasheet_url = await datasheet_link.get_attribute('href', timeout=1000)
                if datasheet_url and not datasheet_url.startswith('http'):
                    datasheet_url = self.base_url + datasheet_url
            except:
                pass
            
            return {
                'part_number': part_number or 'Unknown',
                'manufacturer': manufacturer or 'Unknown',
                'description': description or 'No description',
                'category': category,
                'datasheet_url': datasheet_url,
                'specifications': {},
                'pricing': {'unit_price': price or '$0.00'},
                'availability': {'stock': stock or 'Unknown'},
                'lifecycle_status': 'Active',
                'source': 'DigiKey'
            }
            
        except Exception as e:
            logger.warning(f"Product extraction error: {e}")
            return None
    
    async def _get_text(self, element, selectors: List[str]) -> str:
        """Try multiple selectors to get text content"""
        for selector in selectors:
            try:
                elem = element.locator(selector).first
                if await elem.is_visible(timeout=1000):
                    text = await elem.text_content()
                    return text.strip() if text else ''
            except:
                continue
        return ''


class MouserScraper:
    """Scrapes Mouser for component data"""
    
    def __init__(self, browser: Browser):
        self.browser = browser
        self.base_url = 'https://www.mouser.com'
    
    async def scrape(self, search_term: str, category: str) -> List[Dict]:
        """Scrape Mouser for components"""
        logger.info(f"🔍 Mouser: Searching for '{search_term}'")
        
        page = await self.browser.new_page()
        results = []
        
        try:
            # Navigate to Mouser
            await page.goto(self.base_url, timeout=30000, wait_until='domcontentloaded')
            logger.debug("Mouser homepage loaded")
            
            # Handle cookie consent
            try:
                cookie_button = page.locator('button:has-text("Accept"), button:has-text("I Accept")')
                if await cookie_button.is_visible(timeout=2000):
                    await cookie_button.click()
            except:
                pass
            
            # Search
            search_selectors = [
                'input#SearchInput',
                'input[name="keyword"]',
                'input[placeholder*="Search"]'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = page.locator(selector).first
                    if await search_input.is_visible(timeout=2000):
                        break
                except:
                    continue
            
            if not search_input:
                logger.warning("⚠️ Mouser: Could not find search input")
                return results
            
            await search_input.fill(search_term)
            await search_input.press('Enter')
            logger.debug("Search submitted")
            
            # Wait for results
            try:
                await page.wait_for_selector('.search-result, .result-item, table.SearchResultsTable', timeout=15000)
                logger.debug("Results loaded")
            except PlaywrightTimeout:
                logger.warning("⚠️ Mouser: Timeout waiting for results")
                return results
            
            # Extract products
            product_selectors = [
                '.search-result',
                '.result-item',
                'table.SearchResultsTable tr[id*="row"]'
            ]
            
            products = []
            for selector in product_selectors:
                products = await page.locator(selector).all()
                if products:
                    break
            
            logger.info(f"Found {len(products)} product rows")
            
            # Process each product (limit to top 5)
            for i, product_row in enumerate(products[:5]):
                try:
                    component = await self._extract_mouser_product(product_row, category)
                    if component and component['part_number']:
                        results.append(component)
                        logger.debug(f"Extracted: {component['part_number']}")
                except Exception as e:
                    logger.warning(f"Failed to extract product {i+1}: {e}")
                    continue
            
            logger.info(f"✅ Mouser: Extracted {len(results)} components")
            
        except Exception as e:
            logger.error(f"❌ Mouser scraping error: {e}")
        
        finally:
            await page.close()
        
        return results
    
    async def _extract_mouser_product(self, row, category: str) -> Optional[Dict]:
        """Extract product details from a Mouser row"""
        try:
            # Part number
            part_selectors = [
                '.mfrPartNumber',
                '[data-part-number]',
                'td.mfgNumber'
            ]
            part_number = await self._get_text(row, part_selectors)
            
            # Manufacturer
            mfg_selectors = [
                '.manufacturer',
                '[data-manufacturer]',
                'td.manufacturer'
            ]
            manufacturer = await self._get_text(row, mfg_selectors)
            
            # Description
            desc_selectors = [
                '.description',
                '[data-description]',
                'td.mfrDescription'
            ]
            description = await self._get_text(row, desc_selectors)
            
            # Price
            price_selectors = [
                '.price',
                '[data-price]',
                'td.PriceBreaks'
            ]
            price = await self._get_text(row, price_selectors)
            
            # Stock
            stock_selectors = [
                '.availability',
                '[data-stock]',
                'td.availability'
            ]
            stock = await self._get_text(row, stock_selectors)
            
            return {
                'part_number': part_number or 'Unknown',
                'manufacturer': manufacturer or 'Unknown',
                'description': description or 'No description',
                'category': category,
                'datasheet_url': '',
                'specifications': {},
                'pricing': {'unit_price': price or '$0.00'},
                'availability': {'stock': stock or 'Unknown'},
                'lifecycle_status': 'Active',
                'source': 'Mouser'
            }
            
        except Exception as e:
            logger.warning(f"Product extraction error: {e}")
            return None
    
    async def _get_text(self, element, selectors: List[str]) -> str:
        """Try multiple selectors to get text content"""
        for selector in selectors:
            try:
                elem = element.locator(selector).first
                if await elem.is_visible(timeout=1000):
                    text = await elem.text_content()
                    return text.strip() if text else ''
            except:
                continue
        return ''


async def scrape_components(search_term: str, category: str, use_cache: bool = True) -> Dict:
    """
    Main function to scrape components from DigiKey and Mouser
    
    Args:
        search_term: What to search for
        category: Component category (processor, power_regulator, interface, etc.)
        use_cache: Whether to check cache first
    
    Returns:
        Dict with components and metadata
    """
    logger.info(f"🚀 Starting component search: '{search_term}' ({category})")
    
    # Connect to database
    db = DatabaseManager()
    db.connect()
    
    # Check cache first
    if use_cache:
        cached_components = db.check_cache(search_term, category)
        if cached_components:
            db.disconnect()
            return {
                'cache_hit': True,
                'components': cached_components,
                'search_term': search_term,
                'category': category,
                'total_found': len(cached_components),
                'sources': {'cache': len(cached_components)}
            }
    
    # Scrape from websites
    all_components = []
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        
        # Create scrapers
        digikey = DigiKeyScraper(browser)
        mouser = MouserScraper(browser)
        
        # Run scrapers in parallel
        try:
            digikey_task = asyncio.create_task(digikey.scrape(search_term, category))
            mouser_task = asyncio.create_task(mouser.scrape(search_term, category))
            
            digikey_results, mouser_results = await asyncio.gather(
                digikey_task, 
                mouser_task,
                return_exceptions=True
            )
            
            # Handle results
            if isinstance(digikey_results, list):
                all_components.extend(digikey_results)
            else:
                logger.error(f"DigiKey error: {digikey_results}")
            
            if isinstance(mouser_results, list):
                all_components.extend(mouser_results)
            else:
                logger.error(f"Mouser error: {mouser_results}")
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
        
        finally:
            await browser.close()
    
    # Save to cache
    logger.info(f"💾 Saving {len(all_components)} components to cache")
    for component in all_components:
        db.save_component(component, search_term, category)
    
    db.disconnect()
    
    # Return results
    result = {
        'cache_hit': False,
        'components': all_components,
        'search_term': search_term,
        'category': category,
        'total_found': len(all_components),
        'sources': {
            'digikey': len([c for c in all_components if c['source'] == 'DigiKey']),
            'mouser': len([c for c in all_components if c['source'] == 'Mouser'])
        }
    }
    
    logger.info(f"✅ Search complete: {len(all_components)} components found")
    return result


# ==========================================
# CLI INTERFACE
# ==========================================

if __name__ == '__main__':
    """
    Usage:
        python component_scraper.py "search term" "category"
        python component_scraper.py "STM32F4" "processor"
        python component_scraper.py "buck converter 3.3V" "power_regulator"
    """
    
    if len(sys.argv) < 3:
        print("Usage: python component_scraper.py <search_term> <category>")
        print("Example: python component_scraper.py 'STM32F4' 'processor'")
        sys.exit(1)
    
    search_term = sys.argv[1]
    category = sys.argv[2]
    
    # Run scraper
    result = asyncio.run(scrape_components(search_term, category))
    
    # Print results
    print(json.dumps(result, indent=2))
