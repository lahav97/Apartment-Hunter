import sys
import os

# Add parent directory to path so we can import from our project
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from models.listing import Listing
from filters.rule_filter import RuleFilter


def test_rule_filter():
    """Test the RuleFilter with various listings"""
    print("🔍 Testing RuleFilter...")
    print("=" * 50)

    # Create the filter
    rule_filter = RuleFilter()
    print()

    # Test listings covering all filter criteria
    test_cases = [
        {
            "name": "✅ PERFECT listing",
            "listing": Listing(
                title="דירה מושלמת",
                number_of_rooms=3.0,
                price=3200,
                location="בת גלים",
                description="דירה יפה ומשופצת עם מרפסת",
                url="https://test1.com",
                pets_allowed=True,
                source="yad2",
                contact_phone="052-1111111"
            ),
            "expected": True
        },
        {
            "name": "❌ TOO EXPENSIVE",
            "listing": Listing(
                title="דירה יקרה",
                number_of_rooms=3.0,
                price=5000,  # Above 4000 limit!
                location="בת גלים",
                description="דירה יפה",
                url="https://test2.com",
                pets_allowed=True,
                source="yad2",
                contact_phone="052-2222222"
            ),
            "expected": False
        },
        {
            "name": "❌ TOO CHEAP",
            "listing": Listing(
                title="דירה זולה",
                number_of_rooms=3.0,
                price=2000,  # Below 2500 limit!
                location="בת גלים",
                description="דירה בסיסית",
                url="https://test3.com",
                pets_allowed=True,
                source="yad2",
                contact_phone="052-3333333"
            ),
            "expected": False
        },
        {
            "name": "❌ TOO MANY ROOMS",
            "listing": Listing(
                title="דירה גדולה",
                number_of_rooms=4.5,  # Above 3.5 limit!
                price=3500,
                location="בת גלים",
                description="דירה מרווחת",
                url="https://test4.com",
                pets_allowed=True,
                source="yad2",
                contact_phone="052-4444444"
            ),
            "expected": False
        },
        {
            "name": "❌ TOO FEW ROOMS",
            "listing": Listing(
                title="דירה קטנה",
                number_of_rooms=2.0,  # Below 2.5 limit!
                price=3000,
                location="בת גלים",
                description="דירה נעימה",
                url="https://test5.com",
                pets_allowed=True,
                source="yad2",
                contact_phone="052-5555555"
            ),
            "expected": False
        },
        {
            "name": "❌ WRONG LOCATION",
            "listing": Listing(
                title="דירה במקום רחוק",
                number_of_rooms=3.0,
                price=3200,
                location="תל אביב",  # Not in allowed locations!
                description="דירה יפה",
                url="https://test6.com",
                pets_allowed=True,
                source="yad2",
                contact_phone="052-6666666"
            ),
            "expected": False
        },
        {
            "name": "❌ PETS NOT ALLOWED",
            "listing": Listing(
                title="דירה ללא חיות",
                number_of_rooms=3.0,
                price=3200,
                location="בת גלים",
                description="דירה יפה",
                url="https://test7.com",
                pets_allowed=False,  # You need pets allowed!
                source="yad2",
                contact_phone="052-7777777"
            ),
            "expected": False
        },
        {
            "name": "❌ HAS EXCLUDE KEYWORDS",
            "listing": Listing(
                title="דירה יפה",
                number_of_rooms=3.0,
                price=3200,
                location="בת גלים",
                description="דירה משופצת אסור חיות מחמד",  # Contains exclude keyword!
                url="https://test8.com",
                pets_allowed=True,
                source="yad2",
                contact_phone="052-8888888"
            ),
            "expected": False
        },
        {
            "name": "✅ SECOND LOCATION (נווה שאנן)",
            "listing": Listing(
                title="דירה בנווה שאנן",
                number_of_rooms=2.5,  # Edge case: exactly minimum
                price=2500,  # Edge case: exactly minimum
                location="נווה שאנן",
                description="דירה יפה ומתאימה לחיות מחמד",
                url="https://test9.com",
                pets_allowed=True,
                source="yad2",
                contact_phone="052-9999999"
            ),
            "expected": True
        },
        {
            "name": "✅ EDGE CASE - Maximum values",
            "listing": Listing(
                title="דירה במקסימום",
                number_of_rooms=3.5,  # Edge case: exactly maximum
                price=4000,  # Edge case: exactly maximum
                location="בת גלים",
                description="דירה מעולה",
                url="https://test10.com",
                pets_allowed=True,
                source="yad2",
                contact_phone="052-0000000"
            ),
            "expected": True
        }
    ]

    # Run tests
    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")

        # Run the filter
        result = rule_filter.filter(test_case['listing'])
        expected = test_case['expected']

        # Check if test passed
        if result == expected:
            print(f"   ✅ PASSED - Result: {result}")
            passed += 1
        else:
            print(f"   ❌ FAILED - Expected: {expected}, Got: {result}")
            failed += 1

        # Show listing details for failed tests
        if result != expected:
            listing = test_case['listing']
            print(f"      📋 Listing: {listing.title}")
            print(f"      💰 Price: {listing.price}")
            print(f"      🏠 Rooms: {listing.number_of_rooms}")
            print(f"      📍 Location: {listing.location}")
            print(f"      🐕 Pets: {listing.pets_allowed}")
            print(f"      📝 Description: {listing.description[:50]}...")

        print()

    # Summary
    print("=" * 50)
    print(f"📊 TEST SUMMARY:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed}/{passed + failed} ({passed / (passed + failed) * 100:.1f}%)")


if __name__ == "__main__":
    test_rule_filter()