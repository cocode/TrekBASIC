#!/usr/bin/env python3
"""
Run all tests for TrekBasic - stop at first error
"""
import subprocess
import sys
import re

def run_command(cmd, description):
    """Run a command and return (success, output, test_count)"""
    print(f"\n{description}")
    print("=" * len(description))
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        print(output)
        
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False, ""
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False, ""

def extract_unit_test_count(output):
    """Extract test count from unittest output"""
    match = re.search(r'Ran (\d+) tests', output)
    return int(match.group(1)) if match else 0

def extract_suite_test_count(output):
    """Extract test count from test suite output"""
    match = re.search(r'Results: (\d+) passed', output)
    return int(match.group(1)) if match else 0

def check_unit_test_status(output):
    """Check if unit tests passed and return status message"""
    if "FAILED (" in output:
        failure_match = re.search(r'FAILED \([^)]+\)', output)
        failure_info = failure_match.group(0) if failure_match else "unknown failures"
        return False, f"❌ Unit tests FAILED: {failure_info}"
    elif output.strip().endswith("OK"):
        return True, "✅ Unit tests passed"
    else:
        return False, "❓ Unit test status unclear"

def main():
    print("Running TrekBasic Test Suite")
    print("============================")
    
    total_tests = 0
    
    # 1. Run unit tests
    success, output = run_command(
        "python -m unittest discover -s . -p 'test_*.py' -v",
        "1. Running unit tests..."
    )
    
    unit_tests = extract_unit_test_count(output)
    total_tests += unit_tests
    
    passed, status_msg = check_unit_test_status(output)
    print(status_msg + f" ({unit_tests} tests)")
    
    if not passed:
        sys.exit(1)
    
    # 2. Run BASIC interpreter test suite
    success, output = run_command(
        "python test_suite/run_tests.py",
        "2. Running BASIC interpreter test suite..."
    )
    
    interpreter_tests = extract_suite_test_count(output)
    total_tests += interpreter_tests
    
    # Check for actual failures (not just the word "failed" in "0 failed")
    failed_match = re.search(r'Results: \d+ passed, (\d+) failed', output)
    failed_count = int(failed_match.group(1)) if failed_match else 0
    
    if not success or failed_count > 0:
        print(f"❌ Interpreter tests FAILED ({failed_count} failures)")
        sys.exit(1)
    elif interpreter_tests > 0:
        print(f"✅ Interpreter tests passed ({interpreter_tests} tests)")
    else:
        print("❓ Interpreter test status unclear")
        sys.exit(1)
    
    # 3. Run LLVM compiler test suite
    success, output = run_command(
        "python test_suite/run_llvm_tests.py",
        "3. Running LLVM compiler test suite..."
    )
    
    llvm_tests = extract_suite_test_count(output)
    total_tests += llvm_tests
    
    # Check for actual failures (not just the word "failed" in "0 failed")
    failed_match = re.search(r'Results: \d+ passed, (\d+) failed', output)
    failed_count = int(failed_match.group(1)) if failed_match else 0
    
    if not success or failed_count > 0:
        print(f"❌ LLVM tests FAILED ({failed_count} failures)")
        sys.exit(1)
    elif llvm_tests > 0:
        print(f"✅ LLVM tests passed ({llvm_tests} tests)")
    else:
        print("❓ LLVM test status unclear")
        sys.exit(1)
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Summary:")
    print(f"  Unit tests:        {unit_tests}")
    print(f"  Interpreter tests: {interpreter_tests}")
    print(f"  LLVM tests:        {llvm_tests}")
    print(f"  {'─' * 25}")
    print(f"  Total tests:       {total_tests}")
    print("\nAll tests passed! ✅")

if __name__ == "__main__":
    main() 