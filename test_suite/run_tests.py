#!/usr/bin/env python3
"""
Test runner for BASIC programs in the test_suite directory.
Finds all .bas files, runs them with the BASIC interpreter,
and verifies they return the expected exit code.
"""

import sys
import os
import argparse
from test_runner_common import run_test_suite

def python_command_generator(program_path):
    """Generate command to run a BASIC program with the Python interpreter."""
    return [sys.executable, "basic.py", program_path]

def main():
    parser = argparse.ArgumentParser(description='Run BASIC interpreter tests.')
    parser.add_argument('--include-dir', '-d', action='append', dest='additional_dirs',
                       help='Additional directory to search for .bas files (can be used multiple times)')
    parser.add_argument('--only-dir', '-o', 
                       help='Only run tests from this directory (skip test_suite)')
    args = parser.parse_args()

    # Get the directory containing this script
    test_suite_dir = os.path.dirname(os.path.abspath(__file__))
    
    overall_success = True
    
    if args.only_dir:
        # Only run tests from the specified directory
        if not os.path.exists(args.only_dir):
            print(f"Error: Directory '{args.only_dir}' does not exist")
            sys.exit(1)
        
        success = run_test_suite(args.only_dir, f"Python Interpreter ({os.path.basename(args.only_dir)})", python_command_generator)
        overall_success = success
    else:
        # Run the main test suite
        success = run_test_suite(test_suite_dir, "Python Interpreter (test_suite)", python_command_generator)
        overall_success = success
        
        # Run additional directories if specified
        if args.additional_dirs:
            for additional_dir in args.additional_dirs:
                if not os.path.exists(additional_dir):
                    print(f"Warning: Directory '{additional_dir}' does not exist, skipping")
                    continue
                
                print()  # Add blank line between test suites
                dir_name = os.path.basename(additional_dir)
                success = run_test_suite(additional_dir, f"Python Interpreter ({dir_name})", python_command_generator)
                overall_success = overall_success and success
    
    # Exit with appropriate status
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main() 