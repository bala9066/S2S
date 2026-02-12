#!/usr/bin/env python3
"""
Mouser API Integration
Official API for component search with structured data
"""

import os
import requests
from typing import Dict, List, Optional

class MouserAPI:
    """
    Mouser API Client
    https://www.mouser.com/api-hub/
    """

    def __init__(self):
        self.api_key = os.environ.get('MOUSER_API_KEY')
        self.base_url = 'https://api.mouser.com/api/v1'

    def search_products(
        self,
        keyword: str,
        limit: int = 10
    ) -> Dict:
        """
        Search for products by keyword

        Args:
            keyword: Search term (e.g., "STM32F4", "DC-DC 3.3V")
            limit: Number of results (max 50)

        Returns:
            {
                "success": true,
                "total_found": 15,
                "components": [...]
            }
        """
        try:
            # Mouser API endpoint
            url = f'{self.base_url}/search/keyword'

            # API key in query parameter
            params = {
                'apiKey': self.api_key
            }

            # Search parameters in request body
            payload = {
                'SearchByKeywordRequest': {
                    'keyword': keyword,
                    'records': min(limit, 50),  # Max 50
                    'startingRecord': 0,
                    'searchOptions': 'InStock',  # Only in-stock items
                    'searchWithYourSignUpLanguage': 'en-US'
                }
            }

            response = requests.post(url, params=params, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Parse response
            components = []
            errors = data.get('Errors', [])

            if errors:
                return {
                    'success': False,
                    'cache_hit': False,
                    'search_term': keyword,
                    'total_found': 0,
                    'components': [],
                    'sources': {},
                    'error': f"Mouser API error: {errors[0].get('Message', 'Unknown error')}"
                }

            search_results = data.get('SearchResults', {})
            parts = search_results.get('Parts', [])

            for part in parts:
                # Extract pricing
                pricing = {}
                price_breaks_data = part.get('PriceBreaks', [])
                if price_breaks_data:
                    # Get unit price (first break)
                    unit_price_raw = price_breaks_data[0].get('Price', '0')
                    # Detect currency: ₹ = INR, $ = USD
                    is_inr = '₹' in str(unit_price_raw) or 'INR' in str(unit_price_raw).upper()
                    # Strip ALL non-numeric chars except . for decimal
                    import re
                    price_digits = re.sub(r'[^\d.]', '', str(unit_price_raw))
                    try:
                        unit_price_float = float(price_digits) if price_digits else 0.0
                        # Convert INR to USD (approximate rate)
                        if is_inr and unit_price_float > 0:
                            unit_price_usd = round(unit_price_float / 83.0, 2)
                        else:
                            unit_price_usd = unit_price_float
                        pricing = {
                            'unit_price': f'${unit_price_usd:.2f}',
                            'original_price': str(unit_price_raw),
                            'currency': 'INR' if is_inr else 'USD',
                            'min_qty': price_breaks_data[0].get('Quantity', 1),
                            'price_breaks': [
                                {
                                    'quantity': pb.get('Quantity', 0),
                                    'price': pb.get('Price', '$0.00')
                                }
                                for pb in price_breaks_data
                            ]
                        }
                    except:
                        pricing = {'unit_price': '$0.00', 'original_price': str(unit_price_raw), 'min_qty': 1}

                # Extract availability
                availability = {
                    'stock': int(part.get('AvailabilityInStock', 0)),
                    'lead_time': part.get('LeadTime', 'N/A')
                }

                # Extract specifications
                specifications = {}
                product_attributes = part.get('ProductAttributes', [])
                for attr in product_attributes:
                    attr_name = attr.get('AttributeName', '')
                    attr_value = attr.get('AttributeValue', '')
                    if attr_name and attr_value:
                        specifications[attr_name] = attr_value

                component = {
                    'part_number': part.get('ManufacturerPartNumber', 'Unknown'),
                    'mouser_part_number': part.get('MouserPartNumber', ''),
                    'manufacturer': part.get('Manufacturer', 'Unknown'),
                    'description': part.get('Description', ''),
                    'category': part.get('Category', 'Unknown'),
                    'datasheet_url': part.get('DataSheetUrl', ''),
                    'product_url': part.get('ProductDetailUrl', ''),
                    'specifications': specifications,
                    'pricing': pricing,
                    'availability': availability,
                    'lifecycle_status': part.get('LifecycleStatus', 'Unknown'),
                    'source': 'mouser'
                }

                components.append(component)

            return {
                'success': True,
                'cache_hit': False,
                'search_term': keyword,
                'total_found': search_results.get('NumberOfResult', len(components)),
                'components': components,
                'sources': {'mouser': len(components)}
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'cache_hit': False,
                'search_term': keyword,
                'total_found': 0,
                'components': [],
                'sources': {},
                'error': f'Mouser API error: {str(e)}'
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
    # Test Mouser API
    api = MouserAPI()

    print("Testing Mouser API...")
    print(f"API Key: {api.api_key[:20]}..." if api.api_key else "No API key")

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
