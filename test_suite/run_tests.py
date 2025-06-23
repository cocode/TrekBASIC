#!/usr/bin/env python3
"""
Test runner for BASIC programs in the test_suite directory.
Finds all .bas files, runs them with the BASIC interpreter,
and verifies they return the expected exit code.
"""

import sys
import os
from test_runner_common import run_test_suite

def python_command_generator(program_path):
    """Generate command to run a BASIC program with the Python interpreter."""
    return [sys.executable, "basic.py", program_path]

def main():
    # Get the directory containing this script
    test_suite_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run the test suite
    success = run_test_suite(test_suite_dir, "Python Interpreter", python_command_generator)
    
    # Exit with appropriate status
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 