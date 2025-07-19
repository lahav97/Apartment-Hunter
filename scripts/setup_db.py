#!/usr/bin/env python3
"""
Database setup script for apartment hunter
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import from utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.database import DatabaseManager
from utils.logger import setup_logger


def main():
    """Setup the apartment hunter database"""
    logger = setup_logger(__name__)

    import argparse
    parser = argparse.ArgumentParser(description="Setup apartment hunter database")
    parser.add_argument("--db-path", default="data/listings.db", help="Database file path")
    parser.add_argument("--force", action="store_true", help="Force recreate (deletes existing data)")

    args = parser.parse_args()

    try:
        if args.force and os.path.exists(args.db_path):
            os.remove(args.db_path)
            print(f"🗑️ Deleted existing database: {args.db_path}")

        # Create database manager (will auto-create tables)
        db = DatabaseManager(args.db_path)

        print(f"🎯 Database setup complete!")
        print(f"📍 Location: {os.path.abspath(args.db_path)}")

        # Show database status
        db.print_database_status()

        print(f"\n✅ Ready to run your scraper!")

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()