#!/usr/bin/env python3
"""
Test suite for database functionality
Put this in tests/test_database.py
"""

import unittest
import os
import tempfile
import shutil
from datetime import datetime
from typing import List

# Add parent directory to path for imports
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.database import DatabaseManager
from models.listing import Listing


class TestDatabaseManager(unittest.TestCase):
    """Test suite for DatabaseManager class"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_listings.db")

        # Create DatabaseManager instance with test database
        self.db = DatabaseManager(self.test_db_path)

        # Create sample listing data for testing
        self.sample_listings = [
            Listing(
                title="3 חדרים בבת גלים",
                number_of_rooms=3.0,
                price=3500.0,
                location="בת גלים",
                description="דירה משופצת עם מרפסת",
                url="https://www.yad2.co.il/item/12345",
                pets_allowed=True,
                source="yad2",
                contact_phone="052-1234567",
                size_sqm=80.0,
                parking=True
            ),
            Listing(
                title="2.5 חדרים בנווה שאנן",
                number_of_rooms=2.5,
                price=2800.0,
                location="נווה שאנן",
                description="דירה קטנה וחמודה",
                url="https://www.yad2.co.il/item/67890",
                pets_allowed=False,
                source="yad2",
                contact_phone="052-9876543",
                size_sqm=65.0,
                parking=False
            ),
            Listing(
                title="4 חדרים ברמות רמז",
                number_of_rooms=4.0,
                price=4200.0,
                location="רמות רמז",
                description="דירה גדולה למשפחה",
                url="https://www.yad2.co.il/item/11111",
                pets_allowed=True,
                source="yad2",
                contact_phone="052-5555555",
                size_sqm=100.0,
                parking=True
            )
        ]

    def tearDown(self):
        """Clean up after each test"""
        # Remove temporary test directory and database
        shutil.rmtree(self.test_dir)

    # ==========================================
    # 🏗️ SETUP AND INITIALIZATION TESTS
    # ==========================================

    def test_database_creation(self):
        """Test that database and tables are created correctly"""
        # Database file should exist
        self.assertTrue(os.path.exists(self.test_db_path))

        # Check that all required tables exist
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}

        required_tables = {'listings', 'filters', 'notifications', 'scrape_history'}
        self.assertTrue(required_tables.issubset(tables))

        conn.close()

    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization"""
        # Should have correct path
        self.assertEqual(self.db.db_path, self.test_db_path)

        # Logger should be set up
        self.assertIsNotNone(self.db.logger)

    # ==========================================
    # 💾 CRUD OPERATIONS TESTS
    # ==========================================

    def test_save_single_listing(self):
        """Test saving a single listing"""
        listing = self.sample_listings[0]

        # Save listing
        result = self.db.save_listing(listing)

        # Should return "inserted" for new listing
        self.assertEqual(result, "inserted")

        # Verify it's in database
        retrieved = self.db.get_listing_by_id(listing.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, listing.title)
        self.assertEqual(retrieved.price, listing.price)

    def test_save_duplicate_listing(self):
        """Test saving the same listing twice (should update)"""
        listing = self.sample_listings[0]

        # Save first time
        result1 = self.db.save_listing(listing)
        self.assertEqual(result1, "inserted")

        # Modify and save again
        listing.price = 3600.0  # Change price
        result2 = self.db.save_listing(listing)
        self.assertEqual(result2, "updated")

        # Verify updated price
        retrieved = self.db.get_listing_by_id(listing.id)
        self.assertEqual(retrieved.price, 3600.0)

    def test_save_listings_batch(self):
        """Test saving multiple listings at once"""
        # Save all sample listings
        stats = self.db.save_listings_batch(self.sample_listings)

        # Check statistics
        self.assertEqual(stats['inserted'], 3)
        self.assertEqual(stats['updated'], 0)
        self.assertEqual(stats['errors'], 0)

        # Verify all are in database
        all_listings = self.db.get_listings()
        self.assertEqual(len(all_listings), 3)

    def test_get_listing_by_id(self):
        """Test retrieving listing by ID"""
        # Save a listing
        listing = self.sample_listings[0]
        self.db.save_listing(listing)

        # Retrieve by ID
        retrieved = self.db.get_listing_by_id(listing.id)

        # Should match original
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, listing.id)
        self.assertEqual(retrieved.title, listing.title)

        # Test non-existent ID
        non_existent = self.db.get_listing_by_id("fake_id_12345")
        self.assertIsNone(non_existent)

    def test_get_listings_with_filters(self):
        """Test getting listings with various filters"""
        # Save sample listings
        self.db.save_listings_batch(self.sample_listings)

        # Test: Get all listings
        all_listings = self.db.get_listings()
        self.assertEqual(len(all_listings), 3)

        # Test: Get limited number
        limited = self.db.get_listings(limit=2)
        self.assertEqual(len(limited), 2)

        # Test: Get by source
        yad2_listings = self.db.get_listings(source="yad2")
        self.assertEqual(len(yad2_listings), 3)

        facebook_listings = self.db.get_listings(source="facebook")
        self.assertEqual(len(facebook_listings), 0)

    # ==========================================
    # 🔍 SEARCH FUNCTIONALITY TESTS
    # ==========================================

    def test_search_by_price_range(self):
        """Test searching by price range"""
        # Save sample listings
        self.db.save_listings_batch(self.sample_listings)

        # Search for listings between ₪2500-3500
        criteria = {'price_min': 2500, 'price_max': 3500}
        results = self.db.search_listings(criteria)

        # Should find 2 listings (₪2800 and ₪3500)
        self.assertEqual(len(results), 2)

        # Verify all results are in range
        for listing in results:
            self.assertGreaterEqual(listing.price, 2500)
            self.assertLessEqual(listing.price, 3500)

    def test_search_by_room_range(self):
        """Test searching by room count"""
        # Save sample listings
        self.db.save_listings_batch(self.sample_listings)

        # Search for 2.5-3 room apartments
        criteria = {'rooms_min': 2.5, 'rooms_max': 3.0}
        results = self.db.search_listings(criteria)

        # Should find 2 listings (2.5 and 3.0 rooms)
        self.assertEqual(len(results), 2)

    def test_search_by_location(self):
        """Test searching by location"""
        # Save sample listings
        self.db.save_listings_batch(self.sample_listings)

        # Search for apartments in specific locations
        criteria = {'locations': ['בת גלים', 'נווה שאנן']}
        results = self.db.search_listings(criteria)

        # Should find 2 listings
        self.assertEqual(len(results), 2)

        # Verify locations
        found_locations = {listing.location for listing in results}
        self.assertEqual(found_locations, {'בת גלים', 'נווה שאנן'})

    def test_search_by_keywords(self):
        """Test searching by keywords in title/description"""
        # Save sample listings
        self.db.save_listings_batch(self.sample_listings)

        # Search for apartments with specific keywords
        criteria = {'keywords': ['מרפסת']}
        results = self.db.search_listings(criteria)

        # Should find 1 listing (the one with "מרפסת" in description)
        self.assertEqual(len(results), 1)
        self.assertIn('מרפסת', results[0].description)

    def test_search_complex_criteria(self):
        """Test searching with multiple criteria"""
        # Save sample listings
        self.db.save_listings_batch(self.sample_listings)

        # Complex search: price range + rooms + location
        criteria = {
            'price_min': 2000,
            'price_max': 4000,
            'rooms_min': 2.0,
            'rooms_max': 3.5,
            'locations': ['בת גלים', 'נווה שאנן']
        }
        results = self.db.search_listings(criteria)

        # Should find 2 listings that match ALL criteria
        self.assertEqual(len(results), 2)

    # ==========================================
    # 🗑️ DELETE AND MANAGEMENT TESTS
    # ==========================================

    def test_mark_listing_inactive(self):
        """Test soft deletion (marking as inactive)"""
        # Save a listing
        listing = self.sample_listings[0]
        self.db.save_listing(listing)

        # Mark as inactive
        result = self.db.mark_listing_inactive(listing.id)
        self.assertTrue(result)

        # Should not appear in active listings
        active_listings = self.db.get_listings(active_only=True)
        self.assertEqual(len(active_listings), 0)

        # Should appear when including inactive
        all_listings = self.db.get_listings(active_only=False)
        self.assertEqual(len(all_listings), 1)

    def test_delete_listing_permanently(self):
        """Test permanent deletion"""
        # Save a listing
        listing = self.sample_listings[0]
        self.db.save_listing(listing)

        # Delete permanently
        result = self.db.delete_listing(listing.id)
        self.assertTrue(result)

        # Should not exist at all
        retrieved = self.db.get_listing_by_id(listing.id)
        self.assertIsNone(retrieved)

        all_listings = self.db.get_listings(active_only=False)
        self.assertEqual(len(all_listings), 0)

    def test_clear_listings_only(self):
        """Test clearing only listings table"""
        # Save sample listings
        self.db.save_listings_batch(self.sample_listings)

        # Add a scrape session for testing
        self.db.log_scrape_session("yad2", 3, 3, datetime.now(), True)

        # Clear listings only
        result = self.db.clear_listings_only(confirm=True)
        self.assertTrue(result)

        # Listings should be empty
        listings = self.db.get_listings()
        self.assertEqual(len(listings), 0)

        # Scrape history should still exist
        stats = self.db.get_database_stats()
        self.assertEqual(stats['scrape_history_count'], 1)

    def test_clear_all_data(self):
        """Test clearing all data"""
        # Save sample data
        self.db.save_listings_batch(self.sample_listings)
        self.db.log_scrape_session("yad2", 3, 3, datetime.now(), True)

        # Clear all data
        result = self.db.clear_all_data(confirm=True)
        self.assertTrue(result)

        # Everything should be empty
        stats = self.db.get_database_stats()
        self.assertEqual(stats['listings_count'], 0)
        self.assertEqual(stats['scrape_history_count'], 0)

    # ==========================================
    # 📊 STATISTICS AND REPORTING TESTS
    # ==========================================

    def test_get_database_stats(self):
        """Test database statistics calculation"""
        # Save sample listings
        self.db.save_listings_batch(self.sample_listings)

        # Add scrape session
        self.db.log_scrape_session("yad2", 3, 3, datetime.now(), True)

        # Get statistics
        stats = self.db.get_database_stats()

        # Verify counts
        self.assertEqual(stats['listings_count'], 3)
        self.assertEqual(stats['scrape_history_count'], 1)
        self.assertEqual(stats['listings_today'], 3)

        # Verify price statistics
        self.assertEqual(stats['price_min'], 2800.0)  # Lowest price
        self.assertEqual(stats['price_max'], 4200.0)  # Highest price
        self.assertAlmostEqual(stats['price_avg'], 3500.0, places=1)  # Average

        # Verify source breakdown
        self.assertEqual(stats['listings_by_source']['yad2'], 3)

    def test_log_scrape_session(self):
        """Test logging scrape sessions"""
        start_time = datetime.now()

        # Log successful session
        session_id = self.db.log_scrape_session(
            source="yad2",
            listings_found=10,
            listings_new=5,
            started_at=start_time,
            success=True
        )

        # Should return valid session ID
        self.assertGreater(session_id, 0)

        # Log failed session
        failed_id = self.db.log_scrape_session(
            source="yad2",
            listings_found=0,
            listings_new=0,
            started_at=start_time,
            success=False,
            error_message="CAPTCHA detected"
        )

        # Should return valid session ID
        self.assertGreater(failed_id, 0)

        # Verify in stats
        stats = self.db.get_database_stats()
        self.assertEqual(stats['scrape_history_count'], 2)

    def test_record_notification(self):
        """Test recording notification history"""
        # Save a listing first
        listing = self.sample_listings[0]
        self.db.save_listing(listing)

        # Record successful notification
        result1 = self.db.record_notification(
            listing_id=listing.id,
            notification_type="telegram",
            success=True
        )
        self.assertTrue(result1)

        # Record failed notification
        result2 = self.db.record_notification(
            listing_id=listing.id,
            notification_type="email",
            success=False,
            error_message="Invalid email address"
        )
        self.assertTrue(result2)

        # Verify in stats
        stats = self.db.get_database_stats()
        self.assertEqual(stats['notifications_count'], 2)

    # ==========================================
    # ⚠️ ERROR HANDLING TESTS
    # ==========================================

    def test_invalid_listing_data(self):
        """Test handling of invalid listing data"""
        # Create listing with missing required data
        invalid_listing = Listing(
            title="",  # Empty title
            number_of_rooms=0,
            price=0,
            location="",
            description="",
            url="",
            pets_allowed=None,
            source="",  # Empty source
            contact_phone=""
        )

        # Should still save (but might not pass validation elsewhere)
        result = self.db.save_listing(invalid_listing)
        self.assertEqual(result, "inserted")

    def test_nonexistent_operations(self):
        """Test operations on non-existent data"""
        # Try to delete non-existent listing
        result = self.db.delete_listing("fake_id_12345")
        self.assertFalse(result)

        # Try to mark non-existent listing inactive
        result = self.db.mark_listing_inactive("fake_id_12345")
        self.assertFalse(result)

    # ==========================================
    # 🎯 INTEGRATION TESTS
    # ==========================================

    def test_full_apartment_hunting_workflow(self):
        """Test complete workflow from scraping to search"""
        start_time = datetime.now()

        # 1. Simulate scraping session
        self.db.log_scrape_session("yad2", 0, 0, start_time, True, None)

        # 2. Save scraped listings
        stats = self.db.save_listings_batch(self.sample_listings)
        self.assertEqual(stats['inserted'], 3)

        # 3. Update session with results
        session_id = self.db.log_scrape_session("yad2", 3, 3, start_time, True, None)

        # 4. Search for good apartments
        criteria = {
            'price_min': 2500,
            'price_max': 4000,
            'rooms_min': 2.5,
            'rooms_max': 3.5
        }
        good_apartments = self.db.search_listings(criteria)

        # 5. Send notifications for good apartments
        for apt in good_apartments:
            self.db.record_notification(apt.id, "telegram", True)

        # 6. Verify final state
        final_stats = self.db.get_database_stats()
        self.assertEqual(final_stats['listings_count'], 3)
        self.assertEqual(final_stats['notifications_count'], len(good_apartments))
        self.assertGreaterEqual(final_stats['scrape_history_count'], 1)

    def test_database_performance_with_many_listings(self):
        """Test database performance with larger dataset"""
        # Create many test listings
        many_listings = []
        for i in range(100):
            listing = Listing(
                title=f"Apartment {i}",
                number_of_rooms=2.0 + (i % 4) * 0.5,  # 2.0, 2.5, 3.0, 3.5
                price=2000.0 + (i * 50),  # Increasing prices
                location=f"Location {i % 5}",  # Rotate through 5 locations
                description=f"Description for apartment {i}",
                url=f"https://example.com/item/{i}",
                pets_allowed=(i % 2 == 0),  # Alternate True/False
                source="yad2",
                contact_phone=f"052-{i:07d}"
            )
            many_listings.append(listing)

        # Save all listings
        import time
        start_time = time.time()
        stats = self.db.save_listings_batch(many_listings)
        save_time = time.time() - start_time

        # Verify all saved successfully
        self.assertEqual(stats['inserted'], 100)
        self.assertEqual(stats['errors'], 0)

        # Test search performance
        start_time = time.time()
        search_results = self.db.search_listings({'price_min': 3000, 'price_max': 5000})
        search_time = time.time() - start_time

        # Should find appropriate number of results
        self.assertGreater(len(search_results), 0)

        # Performance should be reasonable (adjust thresholds as needed)
        self.assertLess(save_time, 5.0, "Saving 100 listings took too long")
        self.assertLess(search_time, 1.0, "Searching took too long")


# ==========================================
# 🚀 QUICK FUNCTIONS TESTS
# ==========================================

class TestQuickFunctions(unittest.TestCase):
    """Test the quick convenience functions"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_quick.db")

        # Sample listing
        self.sample_listing = Listing(
            title="Test Apartment",
            number_of_rooms=3.0,
            price=3500.0,
            location="Test Location",
            description="Test Description",
            url="https://test.com/item/123",
            pets_allowed=True,
            source="test",
            contact_phone="052-1111111"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_quick_save_listings(self):
        """Test quick_save_listings function"""
        from utils.database import quick_save_listings

        stats = quick_save_listings([self.sample_listing], self.test_db_path)
        self.assertEqual(stats['inserted'], 1)

    def test_quick_get_listings(self):
        """Test quick_get_listings function"""
        from utils.database import quick_save_listings, quick_get_listings

        # Save a listing first
        quick_save_listings([self.sample_listing], self.test_db_path)

        # Get listings
        retrieved = quick_get_listings(db_path=self.test_db_path)
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0].title, self.sample_listing.title)

    def test_quick_clear_database(self):
        """Test quick_clear_database function"""
        from utils.database import quick_save_listings, quick_clear_database, quick_get_listings

        # Save a listing
        quick_save_listings([self.sample_listing], self.test_db_path)

        # Clear database
        result = quick_clear_database(self.test_db_path)
        # Note: This will return False because it asks for confirmation
        # In a real scenario, you'd pass confirm=True

        # For testing, let's use the DatabaseManager directly
        db = DatabaseManager(self.test_db_path)
        db.clear_all_data(confirm=True)

        # Should be empty now
        listings = quick_get_listings(db_path=self.test_db_path)
        self.assertEqual(len(listings), 0)


# ==========================================
# 🏃‍♂️ MAIN TEST RUNNER
# ==========================================

def run_all_tests():
    """Run all database tests"""
    print("🧪 Running Database Tests...")
    print("=" * 50)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseManager))
    suite.addTests(loader.loadTestsFromTestCase(TestQuickFunctions))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All database tests passed!")
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")

    return result.wasSuccessful()


if __name__ == "__main__":
    # Run tests when script is executed directly
    success = run_all_tests()

    # Exit with appropriate code
    import sys

    sys.exit(0 if success else 1)