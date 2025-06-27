#!/usr/bin/env python3
"""
Run all tests for TrekBasic - stop at first error unless --continue-on-failure is specified
"""
import argparse
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

def extract_unit_test_failures(output):
    """Extract failure count from unittest output"""
    if "FAILED (" in output:
        # Extract failures and errors from patterns like "FAILED (failures=1, errors=10)"
        failure_match = re.search(r'failures=(\d+)', output)
        error_match = re.search(r'errors=(\d+)', output)
        failures = int(failure_match.group(1)) if failure_match else 0
        errors = int(error_match.group(1)) if error_match else 0
        return failures + errors
    return 0

def extract_suite_test_count(output):
    """Extract test count from test suite output"""
    match = re.search(r'Results: (\d+) passed', output)
    return int(match.group(1)) if match else 0

def extract_suite_test_failures(output):
    """Extract failure count from test suite output"""
    failed_match = re.search(r'Results: \d+ passed, (\d+) failed', output)
    return int(failed_match.group(1)) if failed_match else 0

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
    parser = argparse.ArgumentParser(description='Run all TrekBasic tests')
    parser.add_argument('--continue-on-failure', '-c', action='store_true',
                       help='Continue running tests even if some fail')
    args = parser.parse_args()
    
    print("Running TrekBasic Test Suite")
    print("============================")
    if args.continue_on_failure:
        print("Mode: Continue on failure")
    else:
        print("Mode: Stop on first failure")
    
    total_tests = 0
    total_failures = 0
    
    # 1. Run unit tests
    success, output = run_command(
        "python -m unittest discover -s . -p 'test_*.py' -v",
        "1. Running unit tests..."
    )
    
    unit_tests = extract_unit_test_count(output)
    unit_failures = extract_unit_test_failures(output)
    total_tests += unit_tests
    total_failures += unit_failures
    
    passed, status_msg = check_unit_test_status(output)
    print(status_msg + f" ({unit_tests} tests)")
    
    if not passed:
        if not args.continue_on_failure:
            sys.exit(1)
    
    # 2. Run BASIC interpreter test suite
    success, output = run_command(
        "python test_suite/run_tests.py",
        "2. Running BASIC interpreter test suite..."
    )
    
    interpreter_tests = extract_suite_test_count(output)
    interpreter_failures = extract_suite_test_failures(output)
    total_tests += interpreter_tests
    total_failures += interpreter_failures
    
    if not success or interpreter_failures > 0:
        print(f"❌ Interpreter tests FAILED ({interpreter_failures} failures)")
        if not args.continue_on_failure:
            sys.exit(1)
    elif interpreter_tests > 0:
        print(f"✅ Interpreter tests passed ({interpreter_tests} tests)")
    else:
        print("❓ Interpreter test status unclear")
        if not args.continue_on_failure:
            sys.exit(1)
    
    # 3. Run LLVM compiler test suite
    success, output = run_command(
        "python test_suite/run_llvm_tests.py",
        "3. Running LLVM compiler test suite..."
    )
    
    llvm_tests = extract_suite_test_count(output)
    llvm_failures = extract_suite_test_failures(output)
    total_tests += llvm_tests
    total_failures += llvm_failures
    
    if not success or llvm_failures > 0:
        print(f"❌ LLVM tests FAILED ({llvm_failures} failures)")
        if not args.continue_on_failure:
            sys.exit(1)
    elif llvm_tests > 0:
        print(f"✅ LLVM tests passed ({llvm_tests} tests)")
    else:
        print("❓ LLVM test status unclear")
        if not args.continue_on_failure:
            sys.exit(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"{'Section':<20} {'Tests Run':<10} {'Failed':<10}")
    print(f"{'─' * 20} {'─' * 10} {'─' * 10}")
    print(f"{'Unit tests':<20} {unit_tests:<10} {unit_failures:<10}")
    print(f"{'Interpreter tests':<20} {interpreter_tests:<10} {interpreter_failures:<10}")
    print(f"{'LLVM tests':<20} {llvm_tests:<10} {llvm_failures:<10}")
    print(f"{'─' * 20} {'─' * 10} {'─' * 10}")
    print(f"{'TOTAL':<20} {total_tests:<10} {total_failures:<10}")
    
    if total_failures == 0:
        print("\nAll tests passed! ✅")
    else:
        print(f"\n{total_failures} tests failed! ❌")
    
    # Exit with appropriate code
    sys.exit(0 if total_failures == 0 else 1)

if __name__ == "__main__":
    main() 