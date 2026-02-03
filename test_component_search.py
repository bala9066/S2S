#!/usr/bin/env python3
"""
Test script for component search across all suppliers
Tests: DigiKey, Mouser, LCSC
"""

import asyncio
import json
from component_scraper import scrape_components, search_all_suppliers

async def test_single_search():
    """Test single component search across all suppliers"""
    print("=" * 80)
    print("TEST 1: Single Component Search (STM32F4 processor)")
    print("=" * 80)

    result = await scrape_components(
        search_term="STM32F4",
        category="processor",
        use_cache=False  # Force fresh scrape
    )

    print(f"\n✅ Search Complete!")
    print(f"   Total Found: {result['total_found']}")
    print(f"   Cache Hit: {result['cache_hit']}")
    print(f"   Sources: {json.dumps(result['sources'], indent=4)}")

    # Show first component from each supplier
    print("\n📦 Sample Components:")
    for source in ['DigiKey', 'Mouser', 'LCSC']:
        components = [c for c in result['components'] if c['source'] == source]
        if components:
            comp = components[0]
            print(f"\n   {source}:")
            print(f"      Part: {comp['part_number']}")
            print(f"      Mfg: {comp['manufacturer']}")
            print(f"      Desc: {comp['description'][:60]}...")
            print(f"      Price: {comp['pricing'].get('unit_price', 'N/A')}")

    return result


async def test_search_all():
    """Test search_all for multiple components"""
    print("\n" + "=" * 80)
    print("TEST 2: Search All Suppliers (3 component types in parallel)")
    print("=" * 80)

    component_list = [
        {'search_term': 'STM32F4', 'category': 'processor'},
        {'search_term': 'buck converter 3.3V', 'category': 'power_regulator'},
        {'search_term': 'SPI ADC', 'category': 'interface'}
    ]

    result = await search_all_suppliers(
        component_list=component_list,
        use_cache=False
    )

    print(f"\n✅ Search All Complete!")
    print(f"   Total Components: {result['total_components']}")
    print(f"   Total Searches: {result['total_searches']}")
    print(f"   Timestamp: {result['timestamp']}")

    print("\n📊 Results by Component Type:")
    for item in result['results']:
        print(f"\n   {item['search_term']} ({item['category']}):")
        print(f"      Found: {item['total_found']} components")
        print(f"      Sources: {json.dumps(item['sources'], indent=10)}")

    return result


async def test_cache():
    """Test cache functionality"""
    print("\n" + "=" * 80)
    print("TEST 3: Cache Functionality")
    print("=" * 80)

    # First search (miss)
    print("\n🔍 First search (should be cache MISS):")
    result1 = await scrape_components("STM32F7", "processor", use_cache=True)
    print(f"   Cache Hit: {result1['cache_hit']}")
    print(f"   Components: {result1['total_found']}")

    # Second search (hit)
    print("\n🔍 Second search (should be cache HIT):")
    result2 = await scrape_components("STM32F7", "processor", use_cache=True)
    print(f"   Cache Hit: {result2['cache_hit']}")
    print(f"   Components: {result2['total_found']}")

    if result2['cache_hit']:
        print("\n   ✅ Cache is working correctly!")
    else:
        print("\n   ⚠️  Cache might not be working")

    return result2


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("COMPONENT SCRAPER TEST SUITE")
    print("Testing DigiKey, Mouser, and LCSC integration")
    print("=" * 80)

    try:
        # Run tests
        await test_single_search()
        await test_search_all()
        await test_cache()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)
        print("\nVerify:")
        print("  1. All 3 suppliers (DigiKey, Mouser, LCSC) returned results")
        print("  2. Component data includes part number, manufacturer, description, price")
        print("  3. Cache is working (2nd search returns cached data)")
        print("  4. search_all() runs multiple searches in parallel")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
