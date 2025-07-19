#!/usr/bin/env python3
"""
Script to clear/reset the database
"""

import os
import sqlite3
import argparse
from pathlib import Path


def clear_sqlite_database(db_path: str, recreate_tables: bool = False):
    """Clear all data from SQLite database"""
    try:
        if not os.path.exists(db_path):
            print(f"Database file {db_path} does not exist")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found in database")
            conn.close()
            return

        print(f"Found {len(tables)} tables: {[table[0] for table in tables]}")

        # Delete all data from each table
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':
                cursor.execute(f"DELETE FROM {table_name}")
                print(f"✅ Cleared table: {table_name}")

        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence")

        conn.commit()
        conn.close()

        print(f"🎯 Successfully cleared all data from {db_path}")

        if recreate_tables:
            print("Note: Tables structure preserved. Use --drop-tables to recreate schema.")

    except Exception as e:
        print(f"❌ Error clearing database: {e}")


def drop_and_recreate_sqlite(db_path: str):
    """Drop all tables and recreate the database schema"""
    try:
        if not os.path.exists(db_path):
            print(f"Database file {db_path} does not exist")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Drop all tables
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                print(f"🗑️ Dropped table: {table_name}")

        conn.commit()
        conn.close()

        print(f"🎯 Successfully dropped all tables from {db_path}")
        print("💡 Run setup_db.py to recreate the schema")

    except Exception as e:
        print(f"❌ Error dropping tables: {e}")


def delete_database_file(db_path: str):
    """Completely delete the database file"""
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🗑️ Deleted database file: {db_path}")
        else:
            print(f"Database file {db_path} does not exist")
    except Exception as e:
        print(f"❌ Error deleting database file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Clear/reset database")
    parser.add_argument("--db-path", default="data/listings.db", help="Path to database file")
    parser.add_argument("--clear-data", action="store_true", help="Clear all data but keep tables")
    parser.add_argument("--drop-tables", action="store_true", help="Drop all tables")
    parser.add_argument("--delete-file", action="store_true", help="Delete the entire database file")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    if not any([args.clear_data, args.drop_tables, args.delete_file]):
        print("Please specify an action:")
        print("  --clear-data    : Clear all data but keep table structure")
        print("  --drop-tables   : Drop all tables (schema will be lost)")
        print("  --delete-file   : Delete the entire database file")
        return

    # Confirmation
    if not args.confirm:
        print(f"Database: {args.db_path}")
        if args.clear_data:
            print("Action: Clear all data (keep table structure)")
        elif args.drop_tables:
            print("Action: Drop all tables")
        elif args.delete_file:
            print("Action: Delete entire database file")

        response = input("Are you sure? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled")
            return

    # Execute the action
    if args.clear_data:
        clear_sqlite_database(args.db_path)
    elif args.drop_tables:
        drop_and_recreate_sqlite(args.db_path)
    elif args.delete_file:
        delete_database_file(args.db_path)


if __name__ == "__main__":
    main()