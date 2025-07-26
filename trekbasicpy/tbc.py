"""
TrekBasic Compiler (tbc.py) - Compile and run BASIC programs using LLVM
"""
# /// script
# requires-python = ">=3.13"
# dependencies = [
# "llvmlite"
# ]
# ///
import sys
import os
import argparse
import subprocess
import time

env = dict(os.environ)
env["COVERAGE_PROCESS_START"] = ".coveragerc"



from trekbasicpy.basic_loading import load_program
from trekbasicpy.basic_types import BasicSyntaxError
from llvm.codegen import generate_llvm_ir

def main():
    parser = argparse.ArgumentParser(description='Compile and run BASIC programs using LLVM.')
    parser.add_argument('program', help="The name of the basic file to compile and run. Will add '.bas' if not found.")
    parser.add_argument('--keep-files', '-k', action='store_true', 
                       help='Keep intermediate files (.ll and executable)')
    parser.add_argument('--output', '-o', 
                       help='Output executable name (default: <basename>)')
    parser.add_argument('--ir-only', action='store_true',
                       help='Only generate LLVM IR, do not compile or run')
    parser.add_argument('--time', action='store_true',
                       help='Time the execution only (excluding compilation)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug output during LLVM IR generation')
    parser.add_argument('--trace', '-t', action='store_true',
                       help='Enable line-by-line execution tracing')
    args = parser.parse_args()

    # Load and parse the BASIC program
    try:
        program = load_program(args.program)
    except BasicSyntaxError as bse:
        print(f"Syntax Error: {bse.message} in line {bse.line_number}")
        sys.exit(1)
    except FileNotFoundError as f:
        print(f"File not found: {f}")
        sys.exit(1)

    # Generate filenames
    base_name = os.path.splitext(args.program)[0]
    ll_file = f"{base_name}.ll"
    
    if args.output:
        executable_file = args.output
    else:
        executable_file = base_name
    
    try:
        # Step 1: Generate LLVM IR
        print(f"Generating LLVM IR...")
        ir_code = generate_llvm_ir(program, debug=args.debug, trace=args.trace)
        with open(ll_file, "w") as f:
            f.write(ir_code)
        print(f"LLVM IR saved to {ll_file}")
        
        if args.ir_only:
            print("LLVM IR generation complete.")
            sys.exit(0)
        
        # Step 2: Check if clang is available
        try:
            subprocess.run(["clang", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: clang is not available. Please install clang to compile LLVM IR.")
            print("You can still use --ir-only to generate just the LLVM IR file.")
            sys.exit(1)
        
        # Step 3: Compile LLVM IR to executable
        print(f"Compiling to executable...")
        compile_cmd = ["clang", "-o", executable_file, ll_file, "-lm"]
        result = subprocess.run(compile_cmd, capture_output=True, text=True, env=env)
        
        if result.returncode != 0:
            print(f"Compilation failed:")
            print(result.stderr)
            sys.exit(1)
        
        print(f"Executable created: {executable_file}")
        
        # Step 4: Run the executable
        print(f"Running {executable_file}...")
        print("-" * 40)
        
        try:
            # Use the executable path directly (don't prepend ./ for absolute paths)
            if os.path.isabs(executable_file):
                exec_cmd = [executable_file]
            else:
                exec_cmd = [f"./{executable_file}"]
            
            if args.time:
                start_time = time.time()
            result = subprocess.run(exec_cmd, 
                                  capture_output=False, 
                                  text=True)
            if args.time:
                end_time = time.time()
                execution_time = end_time - start_time
            exit_code = result.returncode
        except KeyboardInterrupt:
            print("\nProgram interrupted by user")
            exit_code = 130
        except Exception as e:
            print(f"Error running executable: {e}")
            exit_code = 1
        
        print("-" * 40)
        if args.time:
            print(f"Execution time: {execution_time:.5f} seconds")
        print(f"Program finished with exit code: {exit_code}")
        
        # Step 5: Clean up intermediate files (unless --keep-files)
        if not args.keep_files:
            try:
                if os.path.exists(ll_file):
                    os.remove(ll_file)
                    print(f"Removed {ll_file}")
                if os.path.exists(executable_file):
                    os.remove(executable_file)
                    print(f"Removed {executable_file}")
            except OSError as e:
                print(f"Warning: Could not remove intermediate files: {e}")
        
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"Compilation error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
