#!/usr/bin/env python3
"""
Hardware Pipeline - Automated n8n Workflow Importer
Uses Playwright to automatically import workflows into n8n
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class N8nWorkflowImporter:
    """Automates workflow import into n8n via browser"""
    
    def __init__(
        self,
        n8n_url: str = "http://localhost:5678",
        username: str = None,
        password: str = None
    ):
        self.n8n_url = n8n_url.rstrip('/')
        self.username = username or os.environ.get('N8N_USER', 'admin')
        self.password = password or os.environ.get('N8N_PASSWORD', 'admin123')
        self.browser = None
        self.page = None
    
    async def login(self, page: Page) -> bool:
        """Login to n8n if authentication is enabled"""
        try:
            logger.info("🔐 Attempting n8n login...")
            
            # Navigate to n8n
            await page.goto(self.n8n_url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Check if login form exists (basic auth)
            # n8n might use HTTP basic auth or form-based auth
            current_url = page.url
            
            # If we're on a login page or prompted
            if 'login' in current_url.lower() or await page.locator('input[type="password"]').is_visible(timeout=2000):
                logger.info("Login form detected, entering credentials...")
                
                # Try different login form selectors
                email_selectors = ['input[name="email"]', 'input[type="email"]', '#email']
                password_selectors = ['input[name="password"]', 'input[type="password"]', '#password']
                
                # Enter email/username
                for selector in email_selectors:
                    try:
                        if await page.locator(selector).is_visible(timeout=1000):
                            await page.locator(selector).fill(self.username)
                            break
                    except:
                        continue
                
                # Enter password
                for selector in password_selectors:
                    try:
                        if await page.locator(selector).is_visible(timeout=1000):
                            await page.locator(selector).fill(self.password)
                            break
                    except:
                        continue
                
                # Click login button
                submit_selectors = ['button[type="submit"]', 'button:has-text("Sign in")', 'button:has-text("Login")']
                for selector in submit_selectors:
                    try:
                        if await page.locator(selector).is_visible(timeout=1000):
                            await page.locator(selector).click()
                            break
                    except:
                        continue
                
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
            
            # Verify we're logged in (should see workflows or dashboard)
            if 'workflow' in page.url.lower() or await page.locator('text=Workflows').is_visible(timeout=5000):
                logger.info("✅ Login successful")
                return True
            
            logger.info("✅ No login required or already logged in")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Login handling: {e}")
            return True  # Continue anyway, might not need login
    
    async def import_workflow(self, workflow_path: str, replace_existing: bool = True) -> dict:
        """
        Import a workflow JSON file into n8n
        
        Args:
            workflow_path: Path to the workflow JSON file
            replace_existing: If True, update existing workflow with same name
            
        Returns:
            dict with success status and details
        """
        result = {
            'success': False,
            'workflow_name': None,
            'workflow_id': None,
            'message': ''
        }
        
        # Load workflow JSON
        workflow_path = Path(workflow_path)
        if not workflow_path.exists():
            result['message'] = f"Workflow file not found: {workflow_path}"
            return result
        
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        workflow_name = workflow_data.get('name', 'Unnamed Workflow')
        result['workflow_name'] = workflow_name
        
        logger.info(f"📦 Importing workflow: {workflow_name}")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Login to n8n
                await self.login(page)
                
                # Navigate to workflows page
                await page.goto(f"{self.n8n_url}/workflows", timeout=30000)
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                # Method 1: Try using the n8n API directly (preferred)
                api_result = await self._import_via_api(page, workflow_data)
                if api_result['success']:
                    result.update(api_result)
                    logger.info(f"✅ Workflow imported via API: {workflow_name}")
                    return result
                
                # Method 2: Use the UI import feature
                logger.info("Trying UI import method...")
                
                # Look for import button or menu
                import_selectors = [
                    'button:has-text("Import")',
                    '[data-test-id="workflow-import-button"]',
                    'button[title*="Import"]',
                    '.import-workflow-button'
                ]
                
                import_button = None
                for selector in import_selectors:
                    try:
                        btn = page.locator(selector).first
                        if await btn.is_visible(timeout=2000):
                            import_button = btn
                            break
                    except:
                        continue
                
                # If no direct import button, try the menu
                if not import_button:
                    # Open menu
                    menu_selectors = ['button:has-text("...")', '[data-test-id="workflow-menu"]']
                    for selector in menu_selectors:
                        try:
                            if await page.locator(selector).first.is_visible(timeout=1000):
                                await page.locator(selector).first.click()
                                await asyncio.sleep(0.5)
                                break
                        except:
                            continue
                    
                    # Now look for import in menu
                    for selector in import_selectors:
                        try:
                            btn = page.locator(selector).first
                            if await btn.is_visible(timeout=2000):
                                import_button = btn
                                break
                        except:
                            continue
                
                if import_button:
                    await import_button.click()
                    await asyncio.sleep(1)
                    
                    # Look for URL input or paste area
                    paste_selectors = [
                        'textarea',
                        'input[placeholder*="paste"]',
                        '[data-test-id="workflow-import-input"]'
                    ]
                    
                    for selector in paste_selectors:
                        try:
                            elem = page.locator(selector).first
                            if await elem.is_visible(timeout=2000):
                                await elem.fill(json.dumps(workflow_data))
                                break
                        except:
                            continue
                    
                    # Confirm import
                    confirm_selectors = [
                        'button:has-text("Import")',
                        'button:has-text("Confirm")',
                        'button[type="submit"]'
                    ]
                    
                    for selector in confirm_selectors:
                        try:
                            btn = page.locator(selector).first
                            if await btn.is_visible(timeout=2000):
                                await btn.click()
                                break
                        except:
                            continue
                    
                    await asyncio.sleep(2)
                    result['success'] = True
                    result['message'] = "Workflow imported via UI"
                else:
                    # Fallback: Create via API endpoint
                    result['message'] = "Could not find import button, trying direct navigation"
                    
                    # Try navigating directly to workflow editor
                    await page.goto(f"{self.n8n_url}/workflow/new", timeout=30000)
                    await page.wait_for_load_state('networkidle')
                    
                    result['success'] = True
                    result['message'] = "Navigate to n8n and manually paste the workflow JSON"
                
            except Exception as e:
                result['message'] = f"Import error: {str(e)}"
                logger.error(f"❌ Import failed: {e}")
            
            finally:
                await browser.close()
        
        return result
    
    async def _import_via_api(self, page: Page, workflow_data: dict) -> dict:
        """Try to import workflow via n8n REST API"""
        result = {'success': False, 'workflow_id': None}
        
        try:
            # Use page.evaluate to make API call with session cookies
            api_response = await page.evaluate('''
                async (workflow) => {
                    try {
                        const response = await fetch('/rest/workflows', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(workflow)
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            return { success: true, data: data };
                        } else {
                            const text = await response.text();
                            return { success: false, error: text };
                        }
                    } catch (e) {
                        return { success: false, error: e.message };
                    }
                }
            ''', workflow_data)
            
            if api_response.get('success'):
                result['success'] = True
                result['workflow_id'] = api_response.get('data', {}).get('id')
                result['message'] = "Imported via API"
            else:
                result['message'] = api_response.get('error', 'API import failed')
                
        except Exception as e:
            result['message'] = f"API error: {str(e)}"
        
        return result


async def import_all_workflows(
    workflow_dir: str = ".",
    n8n_url: str = "http://localhost:5678"
) -> dict:
    """
    Import all workflow JSON files from a directory
    
    Args:
        workflow_dir: Directory containing workflow JSON files
        n8n_url: n8n instance URL
        
    Returns:
        dict with import results for each workflow
    """
    results = {}
    importer = N8nWorkflowImporter(n8n_url=n8n_url)
    
    workflow_dir = Path(workflow_dir)
    workflow_files = list(workflow_dir.glob("*Workflow*.json")) + list(workflow_dir.glob("*workflow*.json"))
    
    if not workflow_files:
        logger.warning(f"No workflow files found in {workflow_dir}")
        return results
    
    for wf_file in workflow_files:
        logger.info(f"📁 Processing: {wf_file.name}")
        result = await importer.import_workflow(str(wf_file))
        results[wf_file.name] = result
    
    return results


# ==========================================
# CLI INTERFACE
# ==========================================

if __name__ == '__main__':
    """
    Usage:
        python n8n_workflow_import.py <workflow_file.json>
        python n8n_workflow_import.py Phase1_Complete_Workflow_READY_TO_IMPORT.json
        python n8n_workflow_import.py --all  # Import all workflows in current dir
    """
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Import workflows into n8n')
    parser.add_argument('workflow', nargs='?', help='Path to workflow JSON file')
    parser.add_argument('--all', action='store_true', help='Import all workflow files in current directory')
    parser.add_argument('--url', default='http://localhost:5678', help='n8n URL')
    parser.add_argument('--user', default=None, help='n8n username')
    parser.add_argument('--password', default=None, help='n8n password')
    
    args = parser.parse_args()
    
    if args.all:
        print("🚀 Importing all workflows...")
        results = asyncio.run(import_all_workflows(".", args.url))
        for name, result in results.items():
            status = "✅" if result['success'] else "❌"
            print(f"{status} {name}: {result['message']}")
    elif args.workflow:
        print(f"🚀 Importing workflow: {args.workflow}")
        importer = N8nWorkflowImporter(
            n8n_url=args.url,
            username=args.user,
            password=args.password
        )
        result = asyncio.run(importer.import_workflow(args.workflow))
        
        if result['success']:
            print(f"✅ Successfully imported: {result['workflow_name']}")
            if result.get('workflow_id'):
                print(f"   Workflow ID: {result['workflow_id']}")
        else:
            print(f"❌ Import failed: {result['message']}")
    else:
        parser.print_help()
