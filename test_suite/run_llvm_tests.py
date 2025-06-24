#!/usr/bin/env python3
"""
Test runner for LLVM-compiled BASIC programs in the test_suite directory.
Finds all .bas files, compiles them to LLVM IR, then runs the compiled programs,
and verifies they return the expected exit code.
"""

import sys
import os
import subprocess
from test_runner_common import run_test_suite

def llvm_command_generator(program_path):
    """Generate command to compile and run a BASIC program with LLVM using tbc.py."""
    # Use tbc.py to compile and run the program
    # tbc.py handles the full pipeline: BASIC -> LLVM IR -> executable -> run
    # Since run_llvm_tests.py is run from the project directory, tbc.py is in the current directory
    return [sys.executable, "tbc.py", program_path]

def main():
    # Get the directory containing this script
    test_suite_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if clang is available
    try:
        subprocess.run(["clang", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: clang is not available. Please install clang to run LLVM tests.")
        sys.exit(1)
    
    # Run the test suite
    success = run_test_suite(test_suite_dir, "LLVM Compiler", llvm_command_generator)
    
    # Exit with appropriate status
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 