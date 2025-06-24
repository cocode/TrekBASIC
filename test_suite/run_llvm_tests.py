#!/usr/bin/env python3
"""
Test runner for LLVM-compiled BASIC programs in the test_suite directory.
Finds all .bas files, compiles them to LLVM IR, then runs the compiled programs,
and verifies they return the expected exit code.
"""

import sys
import os
import tempfile
import subprocess
from test_runner_common import run_test_suite

def llvm_command_generator(program_path):
    """Generate command to compile and run a BASIC program with LLVM."""
    # Create a temporary directory for the compiled executable
    temp_dir = tempfile.mkdtemp()
    program_name = os.path.splitext(os.path.basename(program_path))[0]
    
    # The LLVM IR file will be created next to the source file
    program_dir = os.path.dirname(program_path)
    llvm_file = os.path.join(program_dir, f"{program_name}.ll")
    executable_file = os.path.join(temp_dir, program_name)
    
    # Step 1: Generate LLVM IR
    generate_cmd = [sys.executable, "basic.py", program_path, "-l"]
    result = subprocess.run(generate_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to generate LLVM IR: {result.stderr}")
    
    # Step 2: Compile LLVM IR to executable
    compile_cmd = ["clang", "-o", executable_file, llvm_file, "-lm"]
    result = subprocess.run(compile_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to compile LLVM IR: {result.stderr}")
    
    # Step 3: Return command to run the executable
    return [executable_file]

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