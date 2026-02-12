#!/usr/bin/env python3
"""
DigiKey API v3 Integration
Official API for component search with structured data
"""

import os
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class DigiKeyAPI:
    """
    DigiKey API v3 Client
    https://developer.digikey.com/
    """

    def __init__(self):
        self.client_id = os.environ.get('DIGIKEY_CLIENT_ID')
        self.client_secret = os.environ.get('DIGIKEY_CLIENT_SECRET')
        self.base_url = 'https://api.digikey.com'
        self.api_version = 'v3'
        self.access_token = None
        self.token_expires_at = None

    def _get_access_token(self) -> str:
        """
        Get OAuth2 access token.
        Tries in order:
        1. In-memory cached token
        2. Client credentials flow (2-legged, no browser)
        3. Stored token file from 3-legged flow
        4. Refresh token from stored file
        """
        import json

        # 1. Check if in-memory token is still valid
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token

        # 2. Try client_credentials flow first (no browser needed)
        try:
            token = self._client_credentials_flow()
            if token:
                return token
        except Exception:
            pass  # Fall through to stored tokens

        # 3. Load stored tokens from file (from 3-legged auth)
        token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  ".digikey_token.json")
        if not os.path.exists(token_file):
            raise Exception(
                "DigiKey client_credentials failed and no stored tokens. "
                "Run 'python digikey_auth.py' for 3-legged OAuth."
            )

        with open(token_file, "r") as f:
            token_data = json.load(f)

        # Check if stored access token is still valid
        expires_at_str = token_data.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() < expires_at:
                self.access_token = token_data["access_token"]
                self.token_expires_at = expires_at
                return self.access_token

        # 4. Access token expired — use refresh token
        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            raise Exception(
                "DigiKey access token expired and no refresh token available. "
                "Run 'python digikey_auth.py' again."
            )

        token_url = f'{self.base_url}/v1/oauth2/token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }

        response = requests.post(token_url, data=data, timeout=15)
        if response.status_code != 200:
            raise Exception(
                f"DigiKey token refresh failed ({response.status_code}): "
                f"{response.text[:200]}. Run 'python digikey_auth.py' again."
            )

        new_token_data = response.json()

        # Save refreshed tokens
        expires_in = new_token_data.get('expires_in', 3600)
        new_token_data["expires_at"] = (
            datetime.now() + timedelta(seconds=expires_in)
        ).isoformat()
        new_token_data["saved_at"] = datetime.now().isoformat()

        with open(token_file, "w") as f:
            json.dump(new_token_data, f, indent=2)

        self.access_token = new_token_data['access_token']
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
        return self.access_token

    def _client_credentials_flow(self) -> Optional[str]:
        """
        Try OAuth2 client_credentials grant (2-legged, no browser needed).
        Works for DigiKey API v4 Product Search endpoints.
        """
        if not self.client_id or not self.client_secret:
            return None

        token_url = f'{self.base_url}/v1/oauth2/token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
        }

        response = requests.post(token_url, data=data, timeout=15)
        if response.status_code != 200:
            return None

        token_data = response.json()
        expires_in = token_data.get('expires_in', 3600)

        self.access_token = token_data['access_token']
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
        return self.access_token

    def search_products(
        self,
        keyword: str,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> Dict:
        """
        Search for products by keyword

        Args:
            keyword: Search term (e.g., "STM32F4", "DC-DC 3.3V")
            limit: Number of results (max 50)
            filters: Optional filters (e.g., {"InStock": "true"})

        Returns:
            {
                "success": true,
                "total_found": 25,
                "components": [
                    {
                        "part_number": "STM32F407VGT6",
                        "manufacturer": "STMicroelectronics",
                        "description": "ARM Cortex-M4 MCU...",
                        "category": "processor",
                        "datasheet_url": "https://...",
                        "specifications": {...},
                        "pricing": {
                            "unit_price": "$8.50",
                            "min_qty": 1,
                            "price_breaks": [...]
                        },
                        "availability": {
                            "stock": 5000,
                            "lead_time": "2 weeks"
                        },
                        "lifecycle_status": "Active",
                        "source": "digikey"
                    }
                ]
            }
        """
        try:
            token = self._get_access_token()

            # Build request
            url = f'{self.base_url}/Search/{self.api_version}/Products/Keyword'

            headers = {
                'Authorization': f'Bearer {token}',
                'X-DIGIKEY-Client-Id': self.client_id,
                'Content-Type': 'application/json'
            }

            payload = {
                'Keywords': keyword,
                'RecordCount': min(limit, 50),  # API max is 50
                'RecordStartPosition': 0,
                'Filters': filters or {},
                'Sort': {
                    'SortOption': 'SortByUnitPrice',
                    'Direction': 'Ascending'
                },
                'RequestedQuantity': 1
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Parse response
            components = []
            products = data.get('Products', [])

            for product in products:
                # Extract pricing
                pricing = {}
                if product.get('StandardPricing'):
                    price_breaks = product['StandardPricing']
                    if price_breaks:
                        # Get unit price (first break)
                        unit_price = price_breaks[0].get('UnitPrice', 0)
                        pricing = {
                            'unit_price': f'${unit_price:.2f}',
                            'min_qty': price_breaks[0].get('BreakQuantity', 1),
                            'price_breaks': [
                                {
                                    'quantity': pb.get('BreakQuantity', 0),
                                    'price': f"${pb.get('UnitPrice', 0):.2f}"
                                }
                                for pb in price_breaks
                            ]
                        }

                # Extract availability
                availability = {
                    'stock': product.get('QuantityAvailable', 0),
                    'lead_time': product.get('ManufacturerLeadWeeks', 'N/A')
                }

                # Extract specifications
                specifications = {}
                if product.get('Parameters'):
                    for param in product['Parameters']:
                        param_name = param.get('Parameter', '')
                        param_value = param.get('Value', '')
                        if param_name and param_value:
                            specifications[param_name] = param_value

                component = {
                    'part_number': product.get('ManufacturerPartNumber', 'Unknown'),
                    'digikey_part_number': product.get('DigiKeyPartNumber', ''),
                    'manufacturer': product.get('Manufacturer', {}).get('Name', 'Unknown'),
                    'description': product.get('ProductDescription', ''),
                    'category': product.get('Category', {}).get('Name', 'Unknown'),
                    'datasheet_url': product.get('PrimaryDatasheet', ''),
                    'product_url': product.get('ProductUrl', ''),
                    'specifications': specifications,
                    'pricing': pricing,
                    'availability': availability,
                    'lifecycle_status': product.get('ProductStatus', {}).get('Status', 'Unknown'),
                    'source': 'digikey'
                }

                components.append(component)

            return {
                'success': True,
                'cache_hit': False,
                'search_term': keyword,
                'total_found': data.get('ExactManufacturerProductsCount', len(components)),
                'components': components,
                'sources': {'digikey': len(components)}
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'cache_hit': False,
                'search_term': keyword,
                'total_found': 0,
                'components': [],
                'sources': {},
                'error': f'DigiKey API error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'cache_hit': False,
                'search_term': keyword,
                'total_found': 0,
                'components': [],
                'sources': {},
                'error': f'Unexpected error: {str(e)}'
            }


# Test function
if __name__ == '__main__':
    # Test DigiKey API
    api = DigiKeyAPI()

    print("Testing DigiKey API...")
    print(f"Client ID: {api.client_id[:20]}..." if api.client_id else "No client ID")

    # Test search
    result = api.search_products("STM32F4", limit=5)

    print(f"\nSuccess: {result['success']}")
    print(f"Total found: {result['total_found']}")
    print(f"Components returned: {len(result['components'])}")

    if result['components']:
        print("\nFirst component:")
        comp = result['components'][0]
        print(f"  Part: {comp['part_number']}")
        print(f"  Manufacturer: {comp['manufacturer']}")
        print(f"  Price: {comp['pricing'].get('unit_price', 'N/A')}")
        print(f"  Stock: {comp['availability'].get('stock', 0)}")

    if result.get('error'):
        print(f"\nError: {result['error']}")
