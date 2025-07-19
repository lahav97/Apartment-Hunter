import sys
import os
import asyncio

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from scraper.yad2_scraper import Yad2Scraper
from models.listing import Listing


async def test_yad2_scraper_basic():
    """Test basic Yad2Scraper functionality"""
    print("🏠 Testing Yad2Scraper Basic Functionality...")
    print("=" * 50)

    try:
        # Create scraper
        scraper = Yad2Scraper()
        print(f"✅ Scraper created: {scraper}")

        # Test criteria loading
        print(f"✅ Loaded criteria: {scraper.criteria}")

        # Test URL building
        search_url = scraper._build_search_url()
        print(f"✅ Search URL: {search_url}")

        # Test scraper properties
        print(f"✅ Base URL: {scraper.base_url}")
        print(f"✅ Search URL: {scraper.search_url}")

        return scraper

    except Exception as e:
        print(f"❌ Error in basic test: {e}")
        return None


async def test_yad2_scraper_url_building():
    """Test URL building with different parameters"""
    print("\n🔗 Testing URL Building...")
    print("=" * 50)

    try:
        scraper = Yad2Scraper()

        # Test URL building
        url = scraper._build_search_url()
        print(f"✅ Generated URL: {url}")

        # Check if URL contains expected parameters
        if "price_from" in url:
            print("✅ URL contains price_from parameter")
        else:
            print("⚠️  URL missing price_from parameter")

        if "price_to" in url:
            print("✅ URL contains price_to parameter")
        else:
            print("⚠️  URL missing price_to parameter")

        if "city" in url:
            print("✅ URL contains city parameter")
        else:
            print("⚠️  URL missing city parameter")

        return True

    except Exception as e:
        print(f"❌ Error in URL building test: {e}")
        return False


async def test_yad2_scraper_page_fetch():
    """Test fetching a page from Yad2"""
    print("\n🌐 Testing Page Fetching...")
    print("=" * 50)

    try:
        scraper = Yad2Scraper()

        # Build search URL
        search_url = scraper._build_search_url()
        print(f"🔍 Fetching URL: {search_url}")

        # Try to fetch the page
        html_content = await scraper._fetch_page(search_url)

        if html_content:
            print(f"✅ Page fetched successfully!")
            print(f"📄 Content length: {len(html_content)} characters")

            # Check if it looks like a Yad2 page
            if "yad2" in html_content.lower():
                print("✅ Content appears to be from Yad2")
            else:
                print("⚠️  Content doesn't appear to be from Yad2")

            return True
        else:
            print("❌ Failed to fetch page")
            return False

    except Exception as e:
        print(f"❌ Error fetching page: {e}")
        return False
    finally:
        await scraper.close()


async def test_yad2_scraper_real():
    """Test actual scraping from Yad2"""
    print("\n🏗️  Testing Real Yad2 Scraping...")
    print("=" * 50)

    scraper = Yad2Scraper()

    try:
        # This will try to scrape real listings
        print("🔍 Starting scrape...")
        listings = await scraper.scrape()

        print(f"✅ Scraping completed!")
        print(f"📋 Found {len(listings)} listings")

        if listings:
            print(f"\n📊 Sample listings:")
            # Show first few listings
            for i, listing in enumerate(listings[:3]):
                print(f"\n📋 Listing {i + 1}:")
                print(f"   Title: {listing.title}")
                print(f"   Price: {listing.price}₪")
                print(f"   Rooms: {listing.number_of_rooms}")
                print(f"   Location: {listing.location}")
                print(f"   URL: {listing.url}")
                print(f"   Description: {listing.description[:100]}...")

            # Check data quality
            valid_listings = [l for l in listings if l.title and l.price > 0 and l.number_of_rooms > 0]
            print(f"\n✅ Valid listings: {len(valid_listings)}/{len(listings)}")

            if valid_listings:
                print("✅ Found listings with valid data!")
            else:
                print("⚠️  No listings have valid data - may need to update CSS selectors")

        else:
            print("⚠️  No listings found - may need to update CSS selectors or check website structure")

        return listings

    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return []

    finally:
        # Clean up
        await scraper.close()


async def test_extraction_methods():
    """Test individual extraction methods with sample HTML"""
    print("\n🔧 Testing Extraction Methods...")
    print("=" * 50)

    try:
        scraper = Yad2Scraper()

        # Create sample HTML element (this is just for testing the methods)
        from bs4 import BeautifulSoup
        sample_html = """
        <div class="feeditem">
            <h2>דירה יפה בבת גלים</h2>
            <div class="price">3,500₪</div>
            <div class="rooms">3 חדרים</div>
            <div class="location">בת גלים, חיפה</div>
            <a href="/rent/apartment/12345">Link to listing</a>
        </div>
        """

        soup = BeautifulSoup(sample_html, 'html.parser')
        element = soup.find('div', class_='feeditem')

        # Test extraction methods
        title = scraper._extract_title(element)
        price = scraper._extract_price(element)
        rooms = scraper._extract_rooms(element)
        location = scraper._extract_location(element)
        url = scraper._extract_url(element)

        print(f"✅ Title extraction: '{title}'")
        print(f"✅ Price extraction: {price}")
        print(f"✅ Rooms extraction: {rooms}")
        print(f"✅ Location extraction: '{location}'")
        print(f"✅ URL extraction: '{url}'")

        # Check if extractions worked
        success = bool(title and price > 0 and rooms > 0 and location)
        print(f"✅ Extraction test: {'PASSED' if success else 'FAILED'}")

        return success

    except Exception as e:
        print(f"❌ Error in extraction test: {e}")
        return False


async def main():
    """Run all scraper tests"""
    print("🔍 Testing Yad2 Scraper")
    print("=" * 60)

    results = {}

    # Test basic functionality
    print("Phase 1: Basic functionality")
    scraper = await test_yad2_scraper_basic()
    results['basic'] = scraper is not None

    # Test URL building
    print("\nPhase 2: URL building")
    results['url'] = await test_yad2_scraper_url_building()

    # Test page fetching
    print("\nPhase 3: Page fetching")
    results['fetch'] = await test_yad2_scraper_page_fetch()

    # Test extraction methods
    print("\nPhase 4: Extraction methods")
    results['extraction'] = await test_extraction_methods()

    # Test real scraping
    print("\nPhase 5: Real scraping")
    listings = await test_yad2_scraper_real()
    results['scraping'] = len(listings) > 0

    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY:")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper():<15} {status}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\nOverall: {total_passed}/{total_tests} tests passed ({total_passed / total_tests * 100:.1f}%)")

    if results['scraping']:
        print("\n🎉 SUCCESS: Scraper is working and finding listings!")
        print(f"📋 Found {len(listings)} listings from Yad2")
    else:
        print("\n⚠️  PARTIAL SUCCESS: Basic functionality works")
        print("🔧 Need to inspect Yad2 HTML structure and update CSS selectors")

    print("\n💡 Next steps:")
    if not results['scraping']:
        print("   1. Run the scraper and check what HTML structure Yad2 actually uses")
        print("   2. Update CSS selectors in the extraction methods")
        print("   3. Test again")
    else:
        print("   1. Integrate with database and filters")
        print("   2. Add more sophisticated extraction logic")
        print("   3. Build the notification system")


if __name__ == "__main__":
    asyncio.run(main())