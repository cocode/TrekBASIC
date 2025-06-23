#!/usr/bin/env python3
"""
Test runner for BASIC programs in the test_suite directory.
Finds all .bas files, runs them with the BASIC interpreter,
and verifies they return the expected exit code.
"""

import os
import sys
import subprocess
import glob
from pathlib import Path

def find_basic_programs(test_suite_dir):
    """Find all .bas files in the test_suite directory."""
    pattern = os.path.join(test_suite_dir, "*.bas")
    return glob.glob(pattern)

def get_expected_exit_code(program_path):
    """Extract expected exit code from REM comment in first line"""
    try:
        with open(program_path, 'r') as f:
            first_line = f.readline().strip()
            if first_line.startswith('10 REM EXPECT_EXIT_CODE='):
                return int(first_line.split('=')[1])
    except:
        pass
    return 0  # Default to success

def run_basic_program(program_path):
    """Run a BASIC program and return the exit code."""
    try:
        # Run the BASIC interpreter with the program
        result = subprocess.run(
            [sys.executable, "basic.py", program_path],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(program_path))  # Go to project root
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    """Main function to run all BASIC program tests."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all BASIC programs
    basic_programs = find_basic_programs(script_dir)
    
    if not basic_programs:
        print("No BASIC programs found in test_suite directory.")
        return 1
    
    print(f"Found {len(basic_programs)} BASIC program(s) to test:")
    for program in basic_programs:
        print(f"  - {os.path.basename(program)}")
    print()
    
    # Track results
    passed = 0
    failed = 0
    failed_programs = []
    
    # Run each program
    for program_path in sorted(basic_programs):
        program_name = os.path.basename(program_path)
        expected_exit = get_expected_exit_code(program_path)
        print(f"Testing {program_name}...", end=" ")
        
        exit_code, stdout, stderr = run_basic_program(program_path)
        
        if exit_code == expected_exit:
            print("PASS")
            passed += 1
        else:
            print("FAIL")
            print(f"  Expected exit code: {expected_exit}, got: {exit_code}")
            if stdout:
                print(f"  Stdout: {stdout.strip()}")
            if stderr:
                print(f"  Stderr: {stderr.strip()}")
            failed += 1
            failed_programs.append(program_name)
    
    # Print summary
    print("\n" + "="*50)
    print(f"SUMMARY:")
    print(f"  Total programs: {len(basic_programs)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    if failed_programs:
        print(f"  Failed programs: {', '.join(failed_programs)}")
    
    if failed == 0:
        print("All tests PASSED! ✅")
        return 0
    else:
        print(f"{failed} test(s) FAILED! ❌")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 