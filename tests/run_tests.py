#!/usr/bin/env python3
"""Test runner for QuickButtons application."""

import unittest
import sys
import os
import time
from io import StringIO

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_all_tests():
    """Run all tests and return results."""
    # Discover all test files
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(
        start_dir=os.path.dirname(__file__),
        pattern='test_*.py'
    )
    
    # Create test runner
    test_runner = unittest.TextTestRunner(
        verbosity=2,
        stream=StringIO(),
        buffer=True
    )
    
    # Run tests
    start_time = time.time()
    result = test_runner.run(test_suite)
    end_time = time.time()
    
    return result, end_time - start_time

def run_specific_test(test_name):
    """Run a specific test module."""
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromName(f'tests.{test_name}')
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return result

def print_test_summary(result, duration):
    """Print a summary of test results."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Duration: {duration:.2f} seconds")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    print("="*60)

def main():
    """Main function to run tests."""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        print(f"Running specific test: {test_name}")
        result = run_specific_test(test_name)
        print_test_summary(result, 0)
    else:
        # Run all tests
        print("Running all tests...")
        result, duration = run_all_tests()
        print_test_summary(result, duration)
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(main()) 