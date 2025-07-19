import asyncio
import json
from typing import List
from datetime import datetime
from utils.logger import setup_logger
from utils.database import DatabaseManager  # Changed from Database to DatabaseManager
from scraper.yad2_scraper import Yad2Scraper
from filters.rule_filter import RuleFilter
from models.listing import Listing


class ApartmentHunter:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.database = DatabaseManager()  # Using our new DatabaseManager
        self.scraper = Yad2Scraper()
        self.rule_filter = RuleFilter()
        self.settings = self._load_settings()

        self.logger.info("🏠 Apartment Hunter initialized")
        self.logger.info(f"📊 Using filter criteria: {self.rule_filter.criteria}")

    def _load_settings(self) -> dict:
        """Load settings from settings.json"""
        try:
            with open('config/settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            self.logger.info(f"⚙️ Loaded settings: {settings}")
            return settings
        except FileNotFoundError:
            self.logger.warning("⚠️ settings.json not found, using defaults")
            return {
                "interval_minutes": 30,
                "log_level": "INFO",
                "notify_limit": 5,
                "timeout_seconds": 10,
                "retry_attempts": 2
            }

    async def run_single_scan(self) -> dict:
        """Run a single apartment scan cycle"""
        self.logger.info("🔍 Starting apartment scan...")

        results = {
            'scraped': 0,
            'new': 0,
            'filtered': 0,
            'saved': 0,
            'listings': []
        }

        try:
            # Step 1: Scrape listings from Yad2
            self.logger.info("📡 Scraping Yad2...")
            start_time = datetime.now()
            listings = await self.scraper.scrape()
            results['scraped'] = len(listings)

            if not listings:
                self.logger.warning("😞 No listings found - may need to adjust scraper")
                # Log failed scrape session
                self.database.log_scrape_session(
                    source="yad2",
                    listings_found=0,
                    listings_new=0,
                    started_at=start_time,
                    success=False,
                    error_message="No listings found"
                )
                return results

            self.logger.info(f"✅ Found {len(listings)} listings from Yad2")

            # Step 2: Filter out duplicates (already in database)
            new_listings = []
            for listing in listings:
                existing = self.database.get_listing_by_id(listing.id)  # Updated method call
                if not existing:
                    new_listings.append(listing)
                else:
                    self.logger.debug(f"⏭️ Skipping duplicate: {listing.title[:50]}...")

            results['new'] = len(new_listings)

            if not new_listings:
                self.logger.info("📝 All listings are duplicates - no new apartments")
                # Log scrape session with no new listings
                self.database.log_scrape_session(
                    source="yad2",
                    listings_found=len(listings),
                    listings_new=0,
                    started_at=start_time,
                    success=True
                )
                return results

            self.logger.info(f"🆕 Found {len(new_listings)} new listings")

            # Step 3: Apply filters to new listings
            filtered_listings = []
            for listing in new_listings:
                try:
                    if self.rule_filter.filter(listing):
                        filtered_listings.append(listing)
                        self.logger.info(f"✅ PASSED filter: {listing.title} - {listing.price}₪")
                    else:
                        self.logger.debug(f"❌ FAILED filter: {listing.title} - {listing.price}₪")
                except Exception as e:
                    self.logger.error(f"⚠️ Error filtering listing: {e}")
                    continue

            results['filtered'] = len(filtered_listings)
            results['listings'] = filtered_listings

            # Step 4: Save all new listings to database
            save_stats = self.database.save_listings_batch(new_listings)  # Use batch save
            results['saved'] = save_stats['inserted'] + save_stats['updated']

            self.logger.info(f"💾 Database save results: {save_stats}")

            # Log scrape session
            self.database.log_scrape_session(
                source="yad2",
                listings_found=len(listings),
                listings_new=save_stats['inserted'],
                started_at=start_time,
                success=True
            )

            if not filtered_listings:
                self.logger.info("🔍 No listings passed the filters")
                return results

            self.logger.info(f"🎯 {len(filtered_listings)} listings passed filters!")

            # Step 5: Display results
            self._display_good_listings(filtered_listings)

            return results

        except Exception as e:
            self.logger.error(f"💥 Error in scan cycle: {e}")
            # Log failed scrape session
            self.database.log_scrape_session(
                source="yad2",
                listings_found=0,
                listings_new=0,
                started_at=datetime.now(),
                success=False,
                error_message=str(e)
            )
            return results

    def _display_good_listings(self, listings: List[Listing]):
        """Display the good listings that passed filters"""
        self.logger.info("🏆 GREAT APARTMENTS FOUND!")
        self.logger.info("=" * 60)

        for i, listing in enumerate(listings, 1):
            self.logger.info(f"🏠 Apartment {i}:")
            self.logger.info(f"   📍 {listing.title}")
            self.logger.info(f"   💰 {listing.price}₪ per month")
            self.logger.info(f"   🏠 {listing.number_of_rooms} rooms")
            self.logger.info(f"   📍 {listing.location}")
            if listing.url:
                self.logger.info(f"   🔗 {listing.url}")
            if listing.description:
                desc_preview = listing.description[:100] + "..." if len(
                    listing.description) > 100 else listing.description
                self.logger.info(f"   📝 {desc_preview}")
            self.logger.info("")

        self.logger.info("=" * 60)

    async def run_continuous(self):
        """Run apartment hunting continuously"""
        interval_minutes = self.settings.get('interval_minutes', 30)

        self.logger.info(f"🔄 Starting continuous apartment hunting (every {interval_minutes} minutes)")
        self.logger.info("🛑 Press Ctrl+C to stop")

        try:
            while True:
                # Run scan
                results = await self.run_single_scan()

                # Log summary
                self.logger.info(f"📊 Scan complete: {results['scraped']} scraped, "
                                 f"{results['new']} new, {results['filtered']} passed filters, "
                                 f"{results['saved']} saved")

                if results['filtered'] > 0:
                    self.logger.info(f"🎉 Found {results['filtered']} great apartments!")
                else:
                    self.logger.info("😐 No good apartments this time")

                # Show database status
                self.database.print_database_status()

                # Wait for next scan
                self.logger.info(f"⏰ Waiting {interval_minutes} minutes until next scan...")
                await asyncio.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            self.logger.info("🛑 Apartment hunting stopped by user")
        except Exception as e:
            self.logger.error(f"💥 Continuous hunting error: {e}")

    async def test_integration(self):
        """Test the complete integration"""
        self.logger.info("🧪 Testing complete apartment hunting integration...")

        # Test database
        self.logger.info("🔧 Testing database connection...")
        try:
            # Get recent listings (last 24 hours)
            recent_listings = self.database.get_listings(limit=10)
            stats = self.database.get_database_stats()
            self.logger.info(f"✅ Database working - {stats.get('listings_count', 0)} total listings")
            self.logger.info(f"   Recent listings: {len(recent_listings)}")
        except Exception as e:
            self.logger.error(f"❌ Database test failed: {e}")
            return False

        # Test filter
        self.logger.info("🔧 Testing filter system...")
        try:
            test_listing = Listing(
                title="Test apartment",
                number_of_rooms=3.0,
                price=3000,
                location="בת גלים",
                description="Nice apartment",
                url="https://test.com",
                pets_allowed=True,
                source="test",
                contact_phone="052-1234567"
            )

            filter_result = self.rule_filter.filter(test_listing)
            self.logger.info(f"✅ Filter working - test result: {filter_result}")
        except Exception as e:
            self.logger.error(f"❌ Filter test failed: {e}")
            return False

        # Test scraper
        self.logger.info("🔧 Testing scraper...")
        try:
            listings = await self.scraper.scrape()
            self.logger.info(f"✅ Scraper working - found {len(listings)} listings")

            # Show sample URLs to verify they're working
            if listings:
                sample = listings[0]
                self.logger.info(f"   Sample listing: {sample.title[:30]}...")
                self.logger.info(f"   Sample URL: {sample.url}")
        except Exception as e:
            self.logger.error(f"❌ Scraper test failed: {e}")
            return False

        self.logger.info("🎉 All integration tests passed!")
        return True


async def main():
    """Main entry point"""
    hunter = ApartmentHunter()

    # Parse command line arguments (simple version)
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "test":
            # Test integration
            await hunter.test_integration()

        elif command == "scan":
            # Single scan
            results = await hunter.run_single_scan()
            print(f"\n📊 Results: {results['filtered']} good apartments found!")

        elif command == "run":
            # Continuous hunting
            await hunter.run_continuous()

        elif command == "status":
            # Show database status
            hunter.database.print_database_status()

        else:
            print("Usage: python apartment_hunter.py [test|scan|run|status]")
            print("  test   - Test all components")
            print("  scan   - Run single scan")
            print("  run    - Run continuously")
            print("  status - Show database status")
    else:
        # Default: single scan
        results = await hunter.run_single_scan()
        print(f"\n📊 Results: {results['filtered']} good apartments found!")


if __name__ == "__main__":
    asyncio.run(main())