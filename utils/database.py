import sqlite3
import os
from datetime import datetime
from typing import List, Optional

class Database:
    def __init__(self):
        self.db_path = 'data/database.db'
        self._ensure_data_directory()
        self._create_tables()

    def _ensure_data_directory(self):
        os.makedirs("data", exist_ok=True)

    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listings (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    price REAL NOT NULL,
                    number_of_rooms REAL NOT NULL,
                    location TEXT NOT NULL,
                    description TEXT,
                    url TEXT,
                    contact_phone TEXT,
                    pets_allowed INTEGER,
                    source TEXT,
                    scraped_at TEXT,
                    size_sqm REAL,
                    parking INTEGER
                )
            ''')

    def save_listing(self, listing) -> bool:
        """Save a listing to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO listings (
                        id, title, price, number_of_rooms, location, description,
                        url, contact_phone, pets_allowed, source, scraped_at,
                        size_sqm, parking
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    listing.id,
                    listing.title,
                    listing.price,
                    listing.number_of_rooms,
                    listing.location,
                    listing.description,
                    listing.url,
                    listing.contact_phone,
                    listing.pets_allowed,
                    listing.source,
                    listing.scraped_at.isoformat(),
                    listing.size_sqm,
                    listing.parking
                ))

                return True
        except Exception as e:
            return False


    def listing_exists(self, listing_id: str) -> bool:
        """Check if a listing with this ID already exists"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT 1 FROM listings WHERE id = ?', (listing_id,))
                result = cursor.fetchone()

                return result is not None
        except Exception:
            return False

    def get_listing(self, listing_id: str) -> List:
        """Get all listings from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM listings ORDER BY scraped_at DESC')

                return cursor.fetchall()
        except Exception:
            return []

    def get_recent_listings(self, hours: int = 24) -> List:
        """Get listings from the last X hours"""
        try:
            from datetime import datetime, timedelta

            cutoff_time = datetime.now() - timedelta(hours=hours)
            cutoff_str = cutoff_time.isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM listings 
                    WHERE scraped_at > ? 
                    ORDER BY scraped_at DESC
                ''', (cutoff_str,))

                return cursor.fetchall()
        except Exception:
            return []