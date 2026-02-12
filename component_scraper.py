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
    """Scrapes DigiKey for component data using URL-based search"""

    def __init__(self, context):
        self.context = context
        self.base_url = 'https://www.digikey.com'

    async def scrape(self, search_term: str, category: str) -> List[Dict]:
        """Scrape DigiKey for components using direct URL search"""
        logger.info(f"🔍 DigiKey: Searching for '{search_term}'")

        page = await self.context.new_page()
        results = []

        try:
            # Use URL-based search (more reliable than form interaction)
            import urllib.parse
            encoded_term = urllib.parse.quote(search_term)
            search_url = f"{self.base_url}/en/products/result?keywords={encoded_term}"

            logger.debug(f"DigiKey search URL: {search_url}")
            await page.goto(search_url, timeout=45000, wait_until='domcontentloaded')
            logger.debug("DigiKey search results page loaded")

            # Handle cookie consent if present
            try:
                cookie_button = page.locator('button:has-text("Accept"), button:has-text("Accept All")')
                if await cookie_button.is_visible(timeout=3000):
                    await cookie_button.click()
                    await page.wait_for_timeout(1000)
                    logger.debug("Accepted cookies")
            except:
                pass

            # Wait for page to stabilize
            await page.wait_for_timeout(2000)

            # Try multiple result table selectors (DigiKey uses data-testid attributes)
            product_selectors = [
                '[data-testid="search-results-table"] tbody tr',
                'table[data-testid="data-table"] tbody tr',
                '[data-testid="product-table"] tbody tr',
                'table.MuiTable-root tbody tr',
                '#data-table-0 tbody tr',
                '.product-table tbody tr',
                'table tbody tr:has(td)'
            ]

            products = []
            for selector in product_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    products = await page.locator(selector).all()
                    if len(products) > 0:
                        logger.debug(f"Found products using selector: {selector}")
                        break
                except:
                    continue

            if not products:
                # Try extracting from any visible product cards
                logger.debug("Trying card-based selectors...")
                card_selectors = [
                    '[data-testid="product-card"]',
                    '.product-card',
                    'article[data-product]'
                ]
                for selector in card_selectors:
                    try:
                        products = await page.locator(selector).all()
                        if products:
                            break
                    except:
                        continue

            logger.info(f"Found {len(products)} product items")

            # Process each product (limit to top 5)
            for i, product_row in enumerate(products[:5]):
                try:
                    component = await self._extract_digikey_product(product_row, page, category)
                    if component and component['part_number'] and component['part_number'] != 'Unknown':
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
    
    async def _extract_digikey_product(self, row, page, category: str) -> Optional[Dict]:
        """Extract product details from a DigiKey row"""
        try:
            # Get all cells in the row
            cells = await row.locator('td').all()

            part_number = ''
            manufacturer = ''
            description = ''
            price = ''
            stock = ''
            datasheet_url = ''

            # Try to extract from cells by content pattern
            for cell in cells:
                try:
                    text = await cell.text_content(timeout=1000)
                    text = text.strip() if text else ''

                    # Skip empty cells
                    if not text:
                        continue

                    # Check for links (part numbers usually are links)
                    links = await cell.locator('a').all()
                    for link in links:
                        href = await link.get_attribute('href', timeout=500)
                        link_text = await link.text_content(timeout=500)
                        link_text = link_text.strip() if link_text else ''

                        # Datasheet link
                        if href and ('datasheet' in href.lower() or '.pdf' in href.lower()):
                            datasheet_url = href if href.startswith('http') else self.base_url + href
                        # Part number link (to product detail page)
                        elif href and '/product-detail/' in href and link_text:
                            if not part_number:
                                part_number = link_text

                    # Price pattern ($X.XX)
                    if '$' in text and not price:
                        import re
                        price_match = re.search(r'\$[\d,]+\.?\d*', text)
                        if price_match:
                            price = price_match.group()

                    # Stock pattern (numbers with comma)
                    if text.replace(',', '').isdigit() and not stock:
                        stock = text

                except:
                    continue

            # Try specific data-testid selectors as fallback
            if not part_number:
                part_selectors = [
                    '[data-testid="mfr-part-number"] a',
                    '[data-testid="part-number"]',
                    'a[href*="/product-detail/"]'
                ]
                part_number = await self._get_text(row, part_selectors)

            if not manufacturer:
                mfg_selectors = [
                    '[data-testid="manufacturer"]',
                    'td:nth-child(3)',
                    '.manufacturer'
                ]
                manufacturer = await self._get_text(row, mfg_selectors)

            if not description:
                desc_selectors = [
                    '[data-testid="description"]',
                    'td:nth-child(4)',
                    '.description'
                ]
                description = await self._get_text(row, desc_selectors)

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
    """Scrapes Mouser for component data using URL-based search"""

    def __init__(self, context):
        self.context = context
        self.base_url = 'https://www.mouser.com'

    async def scrape(self, search_term: str, category: str) -> List[Dict]:
        """Scrape Mouser for components using direct URL search"""
        logger.info(f"🔍 Mouser: Searching for '{search_term}'")

        page = await self.context.new_page()
        results = []

        try:
            # Use URL-based search (more reliable than form interaction)
            import urllib.parse
            encoded_term = urllib.parse.quote(search_term)
            search_url = f"{self.base_url}/c/?q={encoded_term}"

            logger.debug(f"Mouser search URL: {search_url}")
            await page.goto(search_url, timeout=45000, wait_until='domcontentloaded')
            logger.debug("Mouser search results page loaded")

            # Handle cookie consent
            try:
                cookie_button = page.locator('button:has-text("Accept"), button:has-text("I Accept"), #onetrust-accept-btn-handler')
                if await cookie_button.is_visible(timeout=3000):
                    await cookie_button.click()
                    await page.wait_for_timeout(1000)
                    logger.debug("Accepted cookies")
            except:
                pass

            # Wait for page to stabilize
            await page.wait_for_timeout(2000)

            # Try multiple result selectors
            product_selectors = [
                'table#ctl00_ContentMain_SearchResultsGrid_grid tbody tr',
                'table.SearchResultsTable tbody tr',
                '[data-testid="search-result-row"]',
                '.search-results-row',
                '#gridDiv table tbody tr',
                'table tbody tr:has(a[href*="/ProductDetail/"])'
            ]

            products = []
            for selector in product_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    products = await page.locator(selector).all()
                    if len(products) > 0:
                        logger.debug(f"Found products using selector: {selector}")
                        break
                except:
                    continue

            if not products:
                # Try card-based selectors
                logger.debug("Trying card-based selectors...")
                card_selectors = [
                    '.product-item',
                    '[data-product-id]',
                    'article.product'
                ]
                for selector in card_selectors:
                    try:
                        products = await page.locator(selector).all()
                        if products:
                            break
                    except:
                        continue

            logger.info(f"Found {len(products)} product items")

            # Process each product (limit to top 5)
            for i, product_row in enumerate(products[:5]):
                try:
                    component = await self._extract_mouser_product(product_row, page, category)
                    if component and component['part_number'] and component['part_number'] != 'Unknown':
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
    
    async def _extract_mouser_product(self, row, page, category: str) -> Optional[Dict]:
        """Extract product details from a Mouser row"""
        try:
            # Get all cells in the row
            cells = await row.locator('td').all()

            part_number = ''
            manufacturer = ''
            description = ''
            price = ''
            stock = ''
            datasheet_url = ''

            # Try to extract from cells by content pattern
            for cell in cells:
                try:
                    text = await cell.text_content(timeout=1000)
                    text = text.strip() if text else ''

                    # Skip empty cells
                    if not text:
                        continue

                    # Check for links
                    links = await cell.locator('a').all()
                    for link in links:
                        href = await link.get_attribute('href', timeout=500)
                        link_text = await link.text_content(timeout=500)
                        link_text = link_text.strip() if link_text else ''

                        # Datasheet link
                        if href and ('datasheet' in href.lower() or '.pdf' in href.lower()):
                            datasheet_url = href if href.startswith('http') else self.base_url + href
                        # Part number link (to product detail page)
                        elif href and '/ProductDetail/' in href and link_text:
                            if not part_number:
                                part_number = link_text

                    # Price pattern ($X.XX)
                    if '$' in text and not price:
                        import re
                        price_match = re.search(r'\$[\d,]+\.?\d*', text)
                        if price_match:
                            price = price_match.group()

                    # Stock pattern (In Stock, or numbers)
                    if 'in stock' in text.lower() or 'available' in text.lower():
                        stock = text
                    elif text.replace(',', '').isdigit() and not stock:
                        stock = text

                except:
                    continue

            # Try specific selectors as fallback
            if not part_number:
                part_selectors = [
                    'a[href*="/ProductDetail/"]',
                    '.mfrPartNumber',
                    '[data-part-number]'
                ]
                part_number = await self._get_text(row, part_selectors)

            if not manufacturer:
                mfg_selectors = [
                    'td:nth-child(2)',
                    '.manufacturer',
                    '[data-manufacturer]'
                ]
                manufacturer = await self._get_text(row, mfg_selectors)

            if not description:
                desc_selectors = [
                    'td:nth-child(3)',
                    '.description',
                    '[data-description]'
                ]
                description = await self._get_text(row, desc_selectors)

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


def generate_demo_components(search_term: str, category: str) -> List[Dict]:
    """Generate realistic demo components when real scraping fails"""
    logger.info(f"🎭 Generating demo components for '{search_term}' ({category})")

    # Common component patterns by category
    demo_data = {
        'processor': [
            {'part': 'STM32F407VGT6', 'mfg': 'STMicroelectronics', 'desc': 'ARM Cortex-M4 MCU, 168MHz, 1MB Flash, 192KB RAM', 'price': '$12.50'},
            {'part': 'STM32F446RET6', 'mfg': 'STMicroelectronics', 'desc': 'ARM Cortex-M4 MCU, 180MHz, 512KB Flash, 128KB RAM', 'price': '$8.75'},
            {'part': 'ATSAMD51J19A-AU', 'mfg': 'Microchip', 'desc': 'ARM Cortex-M4F MCU, 120MHz, 512KB Flash', 'price': '$6.20'},
        ],
        'fpga': [
            {'part': 'XC7A35T-1CSG324C', 'mfg': 'AMD/Xilinx', 'desc': 'Artix-7 FPGA, 33K Logic Cells, 324-BGA', 'price': '$45.00'},
            {'part': 'XC7A100T-2FGG484I', 'mfg': 'AMD/Xilinx', 'desc': 'Artix-7 FPGA, 101K Logic Cells, 484-FBGA', 'price': '$85.00'},
            {'part': 'XC7A200T-2FBG484I', 'mfg': 'AMD/Xilinx', 'desc': 'Artix-7 FPGA, 215K Logic Cells, 484-FBGA', 'price': '$120.00'},
            {'part': 'LFE5U-25F-6BG256C', 'mfg': 'Lattice', 'desc': 'ECP5 FPGA, 24K LUTs, 256-BGA', 'price': '$12.00'},
        ],
        'power_regulator': [
            {'part': 'LM2596S-5.0', 'mfg': 'Texas Instruments', 'desc': '3A Step-Down Voltage Regulator, 5V Output', 'price': '$2.50'},
            {'part': 'AP2112K-3.3TRG1', 'mfg': 'Diodes Inc', 'desc': '600mA LDO Regulator, 3.3V Output', 'price': '$0.35'},
            {'part': 'TPS63001DRCR', 'mfg': 'Texas Instruments', 'desc': 'Buck-Boost Converter, 1.8A, Adjustable', 'price': '$3.20'},
            {'part': 'TPS65263RHBR', 'mfg': 'Texas Instruments', 'desc': 'Triple Buck Converter, 1.0V/1.8V/3.3V for FPGA', 'price': '$4.50'},
            {'part': 'LMR36015ADDAR', 'mfg': 'Texas Instruments', 'desc': 'Buck Converter, 36V Input, 1.5A, Adjustable', 'price': '$2.80'},
        ],
        'amplifier': [
            {'part': 'ADL5523ACPZ', 'mfg': 'Analog Devices', 'desc': 'RF/IF Gain Block, 400MHz-4GHz, 21.5dB Gain', 'price': '$8.50'},
            {'part': 'HMC580ALC3B', 'mfg': 'Analog Devices', 'desc': 'GaAs pHEMT MMIC Driver Amp, DC-6GHz, 13dB Gain', 'price': '$12.00'},
            {'part': 'SKY67159-396LF', 'mfg': 'Skyworks', 'desc': 'Wideband LNA, 0.7-3.8GHz, 20dB Gain, 0.6dB NF', 'price': '$2.80'},
            {'part': 'TGF2965-SM', 'mfg': 'Qorvo', 'desc': 'GaN HEMT, DC-18GHz, 10W, 28V, 65% PAE', 'price': '$85.00'},
            {'part': 'TGA2594-SM', 'mfg': 'Qorvo', 'desc': 'GaN PA, 2-18GHz, 4W, 22dB Gain', 'price': '$120.00'},
            {'part': 'HMC1131', 'mfg': 'Analog Devices', 'desc': 'GaAs pHEMT Driver, 6-18GHz, 21dB Gain, 1W', 'price': '$45.00'},
        ],
        'rf_component': [
            {'part': 'ADL5801ACPZ', 'mfg': 'Analog Devices', 'desc': 'Wideband Active Mixer, 10MHz-6GHz, 0.4dB NF', 'price': '$15.00'},
            {'part': 'HMC558ALC3B', 'mfg': 'Analog Devices', 'desc': 'Double-Balanced Mixer, 5.5-14GHz', 'price': '$18.00'},
            {'part': 'BFCN-5500+', 'mfg': 'Mini-Circuits', 'desc': 'Bandpass Filter, 4.9-6.2GHz, LTCC', 'price': '$3.50'},
            {'part': 'QCN-19D+', 'mfg': 'Mini-Circuits', 'desc': 'Directional Coupler, 5-20GHz, 20dB Coupling', 'price': '$6.50'},
            {'part': 'PE42525MLBA-Z', 'mfg': 'pSemi', 'desc': 'RF Switch, SPDT, DC-40GHz, 0.6dB IL', 'price': '$4.20'},
            {'part': 'HMC321ALP4E', 'mfg': 'Analog Devices', 'desc': 'GaAs MMIC SP4T Switch, DC-8GHz', 'price': '$8.00'},
            {'part': 'TQL9065', 'mfg': 'Qorvo', 'desc': 'Ultra-Low Noise LNA, 5-18GHz, 1.2dB NF, 18dB Gain', 'price': '$12.00'},
        ],
        'interface': [
            {'part': 'FT232RL-REEL', 'mfg': 'FTDI', 'desc': 'USB to UART IC, USB 2.0 Full Speed', 'price': '$4.50'},
            {'part': 'MAX3232ECPE+', 'mfg': 'Maxim/Analog', 'desc': 'RS-232 Transceiver, 3.0V-5.5V', 'price': '$2.80'},
            {'part': 'SN65HVD230DR', 'mfg': 'Texas Instruments', 'desc': 'CAN Bus Transceiver, 3.3V', 'price': '$1.20'},
            {'part': 'AD9744ARUZ', 'mfg': 'Analog Devices', 'desc': '14-bit DAC, 210 MSPS, 3.3V', 'price': '$18.00'},
            {'part': 'AD9235BRUZ-65', 'mfg': 'Analog Devices', 'desc': '12-bit ADC, 65 MSPS, 3.3V', 'price': '$12.50'},
        ],
        'connector': [
            {'part': '10118192-0001LF', 'mfg': 'Amphenol', 'desc': 'USB Micro-B Receptacle, SMD', 'price': '$0.45'},
            {'part': '0022035045', 'mfg': 'Molex', 'desc': '4-Pin Header, 2.54mm Pitch', 'price': '$0.25'},
            {'part': '132322-11', 'mfg': 'Amphenol', 'desc': 'SMA Connector, Female, PCB Mount, 50 Ohm', 'price': '$2.50'},
            {'part': '901-10511-2', 'mfg': 'Amphenol', 'desc': 'SMA Connector, Male, Edge-Mount, 18GHz', 'price': '$3.80'},
        ],
        'oscillator': [
            {'part': 'ECS-240-8-36-CKM-TR', 'mfg': 'ECS', 'desc': '24MHz Crystal, 8pF, HC49/SMD', 'price': '$0.35'},
            {'part': 'ABM8-25.000MHZ-B2-T', 'mfg': 'Abracon', 'desc': '25MHz Crystal, 10pF, 3.2x2.5mm', 'price': '$0.50'},
            {'part': 'SIT8008BI-82-33E-100.000000G', 'mfg': 'SiTime', 'desc': 'MEMS Oscillator, 100MHz, 3.3V, 25ppm', 'price': '$2.25'},
            {'part': 'ASTX-H11-100.000MHZ-T', 'mfg': 'Abracon', 'desc': 'TCXO, 100MHz, 2.5ppm, 3.3V', 'price': '$5.50'},
        ],
        'power_amplifier': [
            {'part': 'TGF2965-SM', 'mfg': 'Qorvo', 'desc': 'GaN HEMT, DC-18GHz, 10W, 28V, 65% PAE', 'price': '$85.00'},
            {'part': 'TGA2594-SM', 'mfg': 'Qorvo', 'desc': 'GaN PA, 2-18GHz, 4W, 22dB Gain', 'price': '$120.00'},
            {'part': 'CMPA0060025D', 'mfg': 'Wolfspeed/Cree', 'desc': 'GaN HEMT, DC-6GHz, 25W, 28V', 'price': '$95.00'},
        ],
        'power_input': [
            {'part': 'KPPX-3P', 'mfg': 'Kycon', 'desc': 'DC Power Jack, 2.5mm, Panel Mount', 'price': '$1.20'},
            {'part': 'PJ-037A', 'mfg': 'CUI Devices', 'desc': 'DC Barrel Jack, 2.1mm, SMD', 'price': '$0.85'},
        ]
    }

    # Find matching category or default
    components = demo_data.get(category, demo_data.get('processor', []))

    # Filter by search term if applicable
    search_lower = search_term.lower()
    filtered = [c for c in components if search_lower in c['part'].lower() or search_lower in c['desc'].lower()]

    # If no match, return all from category
    if not filtered:
        filtered = components

    return [
        {
            'part_number': c['part'],
            'manufacturer': c['mfg'],
            'description': c['desc'],
            'category': category,
            'datasheet_url': f"https://www.digikey.com/en/products/detail/{c['part'].lower().replace('-', '')}",
            'specifications': {},
            'pricing': {'unit_price': c['price']},
            'availability': {'stock': 'In Stock (Demo)'},
            'lifecycle_status': 'Active',
            'source': 'Demo Data'
        }
        for c in filtered[:5]
    ]


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
        # Launch browser with stealth settings
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        # Create a context with realistic user agent and viewport
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Create scrapers with context for stealth
        digikey = DigiKeyScraper(context)
        mouser = MouserScraper(context)
        
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
            await context.close()
            await browser.close()
    
    # Fallback to demo data if scraping failed
    use_demo = len(all_components) == 0
    if use_demo:
        logger.warning("⚠️ Real scraping returned 0 results, using demo data fallback")
        all_components = generate_demo_components(search_term, category)

    # Save to cache (only real components, not demo)
    if not use_demo:
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
            'mouser': len([c for c in all_components if c['source'] == 'Mouser']),
            'demo': len([c for c in all_components if c['source'] == 'Demo Data'])
        },
        'demo_mode': use_demo
    }

    logger.info(f"✅ Search complete: {len(all_components)} components found" + (" (demo mode)" if use_demo else ""))
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
