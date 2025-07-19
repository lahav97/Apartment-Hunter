"""
Complete database utilities for apartment hunter
Put this in utils/database.py
"""

import sqlite3
import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models.listing import Listing
from utils.logger import setup_logger


class DatabaseManager:
    """Database manager for apartment hunter application"""

    def __init__(self, db_path: str = "data/listings.db"):
        self.db_path = db_path
        self.logger = setup_logger(__name__)
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Ensure database and tables exist"""
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        if not os.path.exists(self.db_path):
            self.logger.info(f"Creating new database: {self.db_path}")
            self.create_tables()
        else:
            # Check if tables exist, create if missing
            self._create_missing_tables()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def create_tables(self):
        """Create all necessary tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Main listings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id TEXT UNIQUE NOT NULL,  -- Your generated hash ID
                    title TEXT NOT NULL,
                    number_of_rooms REAL,
                    price REAL,
                    location TEXT,
                    description TEXT,
                    url TEXT,
                    pets_allowed BOOLEAN,
                    source TEXT NOT NULL,
                    contact_phone TEXT,
                    size_sqm REAL,
                    parking BOOLEAN,
                    scraped_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # Filters table for storing search criteria
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS filters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price_min REAL,
                    price_max REAL,
                    rooms_min REAL,
                    rooms_max REAL,
                    locations TEXT,  -- JSON string
                    pets_allowed BOOLEAN,
                    keywords_required TEXT,  -- JSON string
                    keywords_excluded TEXT,  -- JSON string
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Notifications tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,  -- 'telegram', 'email', etc.
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT,
                    FOREIGN KEY (listing_id) REFERENCES listings (listing_id)
                )
            ''')

            # Scraping history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scrape_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    listings_found INTEGER DEFAULT 0,
                    listings_new INTEGER DEFAULT 0,
                    listings_updated INTEGER DEFAULT 0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT
                )
            ''')

            # Create indexes for better performance
            self._create_indexes(cursor)

            conn.commit()
            conn.close()

            self.logger.info("Database tables created successfully")

        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            raise

    def _create_indexes(self, cursor):
        """Create database indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_listings_listing_id ON listings(listing_id)",
            "CREATE INDEX IF NOT EXISTS idx_listings_source ON listings(source)",
            "CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price)",
            "CREATE INDEX IF NOT EXISTS idx_listings_rooms ON listings(number_of_rooms)",
            "CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON listings(scraped_at)",
            "CREATE INDEX IF NOT EXISTS idx_listings_active ON listings(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_listing_id ON notifications(listing_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type)",
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

    def _create_missing_tables(self):
        """Check and create any missing tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Check which tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = {row[0] for row in cursor.fetchall()}

            required_tables = {'listings', 'filters', 'notifications', 'scrape_history'}
            missing_tables = required_tables - existing_tables

            if missing_tables:
                self.logger.info(f"Creating missing tables: {missing_tables}")
                conn.close()
                self.create_tables()
            else:
                conn.close()

        except Exception as e:
            self.logger.error(f"Error checking tables: {e}")

    def save_listing(self, listing: Listing) -> bool:
        """
        Save a listing to database (insert or update)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Check if listing already exists
            cursor.execute("SELECT id FROM listings WHERE listing_id = ?", (listing.id,))
            existing = cursor.fetchone()

            if existing:
                # Update existing listing
                cursor.execute('''
                    UPDATE listings SET
                        title = ?, number_of_rooms = ?, price = ?, location = ?,
                        description = ?, url = ?, pets_allowed = ?, source = ?,
                        contact_phone = ?, size_sqm = ?, parking = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE listing_id = ?
                ''', (
                    listing.title, listing.number_of_rooms, listing.price, listing.location,
                    listing.description, listing.url, listing.pets_allowed, listing.source,
                    listing.contact_phone, listing.size_sqm, listing.parking,
                    listing.id
                ))
                self.logger.debug(f"Updated listing: {listing.title[:30]}...")
                result = "updated"
            else:
                # Insert new listing
                cursor.execute('''
                    INSERT INTO listings (
                        listing_id, title, number_of_rooms, price, location,
                        description, url, pets_allowed, source, contact_phone,
                        size_sqm, parking, scraped_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    listing.id, listing.title, listing.number_of_rooms, listing.price,
                    listing.location, listing.description, listing.url, listing.pets_allowed,
                    listing.source, listing.contact_phone, listing.size_sqm, listing.parking,
                    listing.scraped_at
                ))
                self.logger.debug(f"Inserted new listing: {listing.title[:30]}...")
                result = "inserted"

            conn.commit()
            conn.close()
            return result

        except Exception as e:
            self.logger.error(f"Error saving listing: {e}")
            return False

    def save_listings_batch(self, listings: List[Listing]) -> Dict[str, int]:
        """
        Save multiple listings in a batch operation

        Returns:
            dict: Statistics about the operation
        """
        stats = {"inserted": 0, "updated": 0, "errors": 0}

        for listing in listings:
            try:
                result = self.save_listing(listing)
                if result == "inserted":
                    stats["inserted"] += 1
                elif result == "updated":
                    stats["updated"] += 1
                else:
                    stats["errors"] += 1
            except Exception as e:
                self.logger.error(f"Error in batch save: {e}")
                stats["errors"] += 1

        self.logger.info(f"Batch save complete: {stats}")
        return stats

    def get_listing_by_id(self, listing_id: str) -> Optional[Listing]:
        """Get a single listing by its ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM listings WHERE listing_id = ? AND is_active = 1", (listing_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return self._row_to_listing(row)
            return None

        except Exception as e:
            self.logger.error(f"Error getting listing by ID: {e}")
            return None

    def get_listings(self, source: str = None, limit: int = None, active_only: bool = True) -> List[Listing]:
        """
        Get listings from database

        Args:
            source: Filter by source (e.g., 'yad2', 'facebook')
            limit: Maximum number of listings to return
            active_only: Only return active listings

        Returns:
            List of Listing objects
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM listings"
            params = []
            conditions = []

            if active_only:
                conditions.append("is_active = 1")

            if source:
                conditions.append("source = ?")
                params.append(source)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY scraped_at DESC"

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [self._row_to_listing(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error getting listings: {e}")
            return []

    def search_listings(self, criteria: Dict[str, Any]) -> List[Listing]:
        """
        Search listings based on criteria

        Args:
            criteria: Dictionary with search parameters
                - price_min, price_max: Price range
                - rooms_min, rooms_max: Room range
                - locations: List of location strings to match
                - keywords: List of keywords to search in title/description
                - source: Specific source to search

        Returns:
            List of matching Listing objects
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM listings WHERE is_active = 1"
            params = []

            # Price range
            if criteria.get('price_min'):
                query += " AND price >= ?"
                params.append(criteria['price_min'])

            if criteria.get('price_max'):
                query += " AND price <= ?"
                params.append(criteria['price_max'])

            # Room range
            if criteria.get('rooms_min'):
                query += " AND number_of_rooms >= ?"
                params.append(criteria['rooms_min'])

            if criteria.get('rooms_max'):
                query += " AND number_of_rooms <= ?"
                params.append(criteria['rooms_max'])

            # Source
            if criteria.get('source'):
                query += " AND source = ?"
                params.append(criteria['source'])

            # Location (basic string matching)
            if criteria.get('locations'):
                location_conditions = []
                for location in criteria['locations']:
                    location_conditions.append("location LIKE ?")
                    params.append(f"%{location}%")
                query += " AND (" + " OR ".join(location_conditions) + ")"

            # Keywords (search in title and description)
            if criteria.get('keywords'):
                keyword_conditions = []
                for keyword in criteria['keywords']:
                    keyword_conditions.append("(title LIKE ? OR description LIKE ?)")
                    params.extend([f"%{keyword}%", f"%{keyword}%"])
                query += " AND (" + " OR ".join(keyword_conditions) + ")"

            query += " ORDER BY scraped_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [self._row_to_listing(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error searching listings: {e}")
            return []

    def _row_to_listing(self, row) -> Listing:
        """Convert database row to Listing object"""
        # Create listing object with the same parameters your class expects
        listing = Listing(
            title=row['title'],
            number_of_rooms=row['number_of_rooms'],
            price=row['price'],
            location=row['location'],
            description=row['description'],
            url=row['url'],
            pets_allowed=row['pets_allowed'],
            source=row['source'],
            contact_phone=row['contact_phone'],
            size_sqm=row['size_sqm'],
            parking=row['parking']
        )

        # Override the generated ID and scraped_at with database values
        listing.id = row['listing_id']
        listing.scraped_at = datetime.fromisoformat(row['scraped_at']) if row['scraped_at'] else datetime.now()

        return listing

    def mark_listing_inactive(self, listing_id: str) -> bool:
        """Mark a listing as inactive (soft delete)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE listings SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE listing_id = ?",
                (listing_id,)
            )

            affected = cursor.rowcount
            conn.commit()
            conn.close()

            if affected > 0:
                self.logger.info(f"Marked listing {listing_id} as inactive")
                return True
            else:
                self.logger.warning(f"No listing found with ID {listing_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error marking listing inactive: {e}")
            return False

    def delete_listing(self, listing_id: str) -> bool:
        """Permanently delete a listing"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM listings WHERE listing_id = ?", (listing_id,))

            affected = cursor.rowcount
            conn.commit()
            conn.close()

            if affected > 0:
                self.logger.info(f"Deleted listing {listing_id}")
                return True
            else:
                self.logger.warning(f"No listing found with ID {listing_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error deleting listing: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            stats = {}

            # Table counts
            tables = ['listings', 'filters', 'notifications', 'scrape_history']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]

            # Listings by source
            cursor.execute("SELECT source, COUNT(*) FROM listings WHERE is_active = 1 GROUP BY source")
            stats['listings_by_source'] = dict(cursor.fetchall())

            # Recent activity
            cursor.execute("SELECT COUNT(*) FROM listings WHERE date(scraped_at) = date('now')")
            stats['listings_today'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM listings WHERE date(scraped_at) >= date('now', '-7 days')")
            stats['listings_this_week'] = cursor.fetchone()[0]

            # Price statistics
            cursor.execute("SELECT MIN(price), MAX(price), AVG(price) FROM listings WHERE is_active = 1 AND price > 0")
            price_stats = cursor.fetchone()
            if price_stats:
                stats['price_min'] = price_stats[0]
                stats['price_max'] = price_stats[1]
                stats['price_avg'] = round(price_stats[2], 2) if price_stats[2] else 0

            conn.close()
            return stats

        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}

    def clear_all_data(self, confirm: bool = False) -> bool:
        """Clear all data from all tables but keep structure"""
        if not confirm:
            response = input(f"Clear all data from {self.db_path}? (y/N): ")
            if response.lower() != 'y':
                print("Cancelled")
                return False

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            # Clear each table
            for table in tables:
                table_name = table[0]
                if table_name != 'sqlite_sequence':
                    cursor.execute(f"DELETE FROM {table_name}")
                    self.logger.info(f"Cleared table: {table_name}")

            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence")

            conn.commit()
            conn.close()

            self.logger.info(f"Successfully cleared all data from {self.db_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error clearing database: {e}")
            return False

    def clear_listings_only(self, confirm: bool = False) -> bool:
        """Clear only the listings table"""
        if not confirm:
            response = input(f"Clear listings table from {self.db_path}? (y/N): ")
            if response.lower() != 'y':
                print("Cancelled")
                return False

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM listings")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='listings'")

            conn.commit()
            conn.close()

            self.logger.info("Successfully cleared listings table")
            return True

        except Exception as e:
            self.logger.error(f"Error clearing listings table: {e}")
            return False

    def print_database_status(self):
        """Print current database status"""
        if not os.path.exists(self.db_path):
            print(f"❌ Database file {self.db_path} does not exist")
            return

        stats = self.get_database_stats()
        if not stats:
            print(f"📊 Database {self.db_path} - unable to get stats")
            return

        print(f"📊 Database Status: {self.db_path}")
        print("=" * 50)
        print(f"  📋 Total listings: {stats.get('listings_count', 0):,}")
        print(f"  📅 Added today: {stats.get('listings_today', 0):,}")
        print(f"  📈 Added this week: {stats.get('listings_this_week', 0):,}")
        print(f"  🔔 Notifications sent: {stats.get('notifications_count', 0):,}")
        print(f"  🔄 Scrape sessions: {stats.get('scrape_history_count', 0):,}")

        if stats.get('listings_by_source'):
            print(f"  📊 By source:")
            for source, count in stats['listings_by_source'].items():
                print(f"     {source}: {count:,}")

        if stats.get('price_min'):
            print(f"  💰 Price range: ₪{stats.get('price_min', 0):,.0f} - ₪{stats.get('price_max', 0):,.0f}")
            print(f"  📊 Average price: ₪{stats.get('price_avg', 0):,.0f}")

        print("=" * 50)

    def log_scrape_session(self, source: str, listings_found: int, listings_new: int,
                          started_at: datetime, success: bool = True, error_message: str = None) -> int:
        """Log a scraping session"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO scrape_history (
                    source, listings_found, listings_new, started_at, 
                    success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (source, listings_found, listings_new, started_at, success, error_message))

            session_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return session_id

        except Exception as e:
            self.logger.error(f"Error logging scrape session: {e}")
            return 0

    def record_notification(self, listing_id: str, notification_type: str,
                           success: bool = True, error_message: str = None) -> bool:
        """Record that a notification was sent for a listing"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO notifications (
                    listing_id, notification_type, success, error_message
                ) VALUES (?, ?, ?, ?)
            ''', (listing_id, notification_type, success, error_message))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            self.logger.error(f"Error recording notification: {e}")
            return False


# Convenience functions for quick operations
def quick_save_listings(listings: List[Listing], db_path: str = "data/listings.db") -> Dict[str, int]:
    """Quick function to save listings"""
    db = DatabaseManager(db_path)
    return db.save_listings_batch(listings)


def quick_get_listings(source: str = None, limit: int = 50, db_path: str = "data/listings.db") -> List[Listing]:
    """Quick function to get listings"""
    db = DatabaseManager(db_path)
    return db.get_listings(source=source, limit=limit)


def quick_database_status(db_path: str = "data/listings.db"):
    """Quick function to show database status"""
    db = DatabaseManager(db_path)
    db.print_database_status()


def quick_clear_database(db_path: str = "data/listings.db"):
    """Quick function to clear database"""
    db = DatabaseManager(db_path)
    return db.clear_all_data()