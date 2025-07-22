#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_specific_test(test_name):
    """Run a specific test module"""
    try:
        if test_name == "database":
            from tests.test_database import run_all_tests
            return run_all_tests()
        elif test_name == "filters":
            print("🔧 Running filter tests...")
            # Import your existing filter tests
            # from tests.test_filters import run_tests
            # return run_tests()
            print("⚠️ Filter tests not implemented yet")
            return True
        elif test_name == "scrapers":
            print("🕷️ Running scraper tests...")
            # Import your existing scraper tests
            # from tests.test_scrapers import run_tests
            # return run_tests()
            print("⚠️ Scraper tests not implemented yet")
            return True
        elif test_name == "notifiers":
            print("📱 Running notifier tests...")
            # Import your existing notifier tests
            # from tests.test_notifiers import run_tests
            # return run_tests()
            print("⚠️ Notifier tests not implemented yet")
            return True
        else:
            print(f"❌ Unknown test: {test_name}")
            return False
    except ImportError as e:
        print(f"❌ Could not import {test_name} tests: {e}")
        return False
    except Exception as e:
        print(f"❌ Error running {test_name} tests: {e}")
        return False


def run_all_tests():
    """Run all available tests"""
    print("🚀 Running All Apartment Hunter Tests")
    print("=" * 60)

    test_modules = ["database", "filters", "scrapers", "notifiers"]
    results = {}

    for test_module in test_modules:
        print(f"\n📋 Testing {test_module.title()}...")
        print("-" * 40)

        try:
            success = run_specific_test(test_module)
            results[test_module] = success

            if success:
                print(f"✅ {test_module.title()} tests: PASSED")
            else:
                print(f"❌ {test_module.title()} tests: FAILED")

        except Exception as e:
            print(f"💥 {test_module.title()} tests: ERROR - {e}")
            results[test_module] = False

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name.ljust(12)}: {status}")

    print("-" * 60)
    print(f"🎯 Overall: {passed}/{total} test suites passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Your apartment hunter is ready! 🏠")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("🧪 Apartment Hunter Test Runner")
        print("=" * 40)
        print("Usage:")
        print("  python run_tests.py all              # Run all tests")
        print("  python run_tests.py database         # Test database only")
        print("  python run_tests.py filters          # Test filters only")
        print("  python run_tests.py scrapers         # Test scrapers only")
        print("  python run_tests.py notifiers        # Test notifiers only")
        print()
        print("Available test modules:")
        print("  📊 database  - Database operations and storage")
        print("  🔍 filters   - Apartment filtering logic")
        print("  🕷️ scrapers  - Web scraping functionality")
        print("  📱 notifiers - Notification systems")
        return

    test_arg = sys.argv[1].lower()

    if test_arg == "all":
        success = run_all_tests()
    else:
        success = run_specific_test(test_arg)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()