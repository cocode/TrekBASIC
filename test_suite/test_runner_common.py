#!/usr/bin/env python3
"""
Common test runner logic shared between Python interpreter and LLVM tests.
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
            if (equals := first_line.find("@EXPECT_EXIT_CODE") != -1):
                value = first_line[:equals]
                return int(value)
    except (FileNotFoundError, ValueError, IndexError):
        pass
    return 0  # Default to 0 (success)

def run_test_with_command(command, program_path, expected_exit_code):
    """Run a test with the given command and check the exit code."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        actual_exit_code = result.returncode
        
        if actual_exit_code == expected_exit_code:
            return True, None, actual_exit_code
        else:
            error_msg = f"Expected exit code: {expected_exit_code}, got: {actual_exit_code}"
            if result.stdout:
                error_msg += f"\n  Stdout: {result.stdout.strip()}"
            if result.stderr:
                error_msg += f"\n  Stderr: {result.stderr.strip()}"
            return False, error_msg, actual_exit_code
            
    except subprocess.TimeoutExpired:
        return False, "Test timed out after 30 seconds", None
    except Exception as e:
        return False, f"Error running test: {str(e)}", None

def run_test_suite(test_suite_dir, test_runner_name, command_generator):
    """
    Run a test suite using the provided command generator.
    
    Args:
        test_suite_dir: Directory containing .bas files
        test_runner_name: Name for display purposes (e.g., "Python", "LLVM")
        command_generator: Function that takes a program path and returns the command to run
    """
    print(f"Running {test_runner_name} test suite...")
    print("=" * 50)
    
    programs = find_basic_programs(test_suite_dir)
    if not programs:
        print("No BASIC programs found!")
        return False
    
    passed = 0
    failed = 0
    
    for program_path in sorted(programs):
        program_name = os.path.basename(program_path)
        expected_exit_code = get_expected_exit_code(program_path)
        
        print(f"Testing {program_name}...", end=" ")
        
        command = command_generator(program_path)
        success, error_msg, actual_exit_code = run_test_with_command(command, program_path, expected_exit_code)
        
        if success:
            print("PASS")
            passed += 1
        else:
            print("FAIL")
            print(f"  {error_msg}")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0 