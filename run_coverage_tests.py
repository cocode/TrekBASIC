#!/usr/bin/env python3
"""
Run tests with coverage - avoids nested coverage issues by running test suites directly
"""
import subprocess
import sys
import os
import glob

env = dict(os.environ)
env["COVERAGE_PROCESS_START"] = ".coveragerc"

def run_with_coverage(cmd_args, description):
    """Run a command with coverage and return success status"""
    print(f"\n{description}")
    print("=" * len(description))
    
    # coverage_cmd = [sys.executable, "-m", "coverage", "run", "--parallel-mode"] + cmd.split()

    coverage_cmd = [sys.executable, "-m", "coverage", "run", "--parallel-mode"] + cmd_args

    print(f"Running {' '.join(coverage_cmd)}")
    try:
        result = subprocess.run(
            coverage_cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        print("RESULT: ", result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def run_basic_tests_with_coverage(test_suite_dir):
    """Run BASIC tests directly with coverage"""
    print(f"\nRunning BASIC tests from {test_suite_dir}")
    print("=" * 50)
    
    # Find all .bas files
    pattern = os.path.join(test_suite_dir, "*.bas")
    bas_files = glob.glob(pattern)
    
    if not bas_files:
        print("No BASIC files found!")
        return True
    
    passed = 0
    failed = 0
    
    for bas_file in sorted(bas_files):
        bas_name = os.path.basename(bas_file)
        print(f"Testing {bas_name}...", end=" ")
        
        # Run the BASIC file directly with coverage
        cmd = ["-m",  "trekbasicpy.basic", bas_file]
        success = run_with_coverage(cmd, f"Running {bas_name}")
        
        if success:
            print("PASS")
            passed += 1
        else:
            print("FAIL")
            failed += 1
    
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_coverage_tests.py <test_suite_dir>")
        print("Example: python run_coverage_tests.py ~/source/basic_test_suite")
        sys.exit(1)
    
    test_suite_dir = sys.argv[1]
    
    if not os.path.exists(test_suite_dir):
        print(f"Error: Test suite directory '{test_suite_dir}' does not exist")
        sys.exit(1)
    
    print("Running tests with coverage...")
    print("=" * 50)
    
    # Run unit tests
    success1 = run_with_coverage(
        ["-m", "unittest", "discover", "-s", "test", "-p", "test_*.py", "-v"],
        "1. Running unit tests..."
    )
    
    # Run BASIC tests directly with coverage
    success2 = run_basic_tests_with_coverage(test_suite_dir)
    
    # Run LLVM tests (without coverage since they create native executables)
    # We should get coverage data on the file coverage.py, but we don't currently
    # even check code in that directory. As written below, it doens't change the coverage stats at all.
    # success3 = run_with_coverage(
    #     ["run_llvm_tests.py", "--test-suite-dir", test_suite_dir],
    #     "3. Running LLVM tests..."
    # )
    
    # Combine coverage data
    print("\nCombining coverage data...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "coverage", "combine"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        if result.returncode == 0:
            print("✅ Coverage data combined successfully")
        else:
            print(f"⚠️  Warning: Failed to combine coverage data: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Warning: Error combining coverage data: {e}")
    
    # Show coverage report
    print("\nCoverage Report:")
    print("=" * 20)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "coverage", "report"],
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        print(result.stdout)
    except Exception as e:
        print(f"⚠️  Warning: Error generating coverage report: {e}")
    
    overall_success = success1 and success2 and success3
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main() 