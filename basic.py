"""
Main program for running a basic program from the command line.
"""
import sys
import argparse
import pprint
import traceback

from basic_interpreter import Executor
from basic_loading import load_program
from basic_types import BasicSyntaxError, RunStatus
from llvm.codegen import generate_llvm_ir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run BASIC programs.')
    parser.add_argument('program', help="The name of the basic file to run. Will add '.bas' of not found.")
    parser.add_argument('--trace', '-t', action='store_true', help="Write  a trace of execution to 'tracefile.txt'.")
    parser.add_argument('--symbols', '-s', action='store_true', help="Dump the symbol table on exit.")
    parser.add_argument(
        '-l', '--llvm',
        action='store_true',
        help='Save the basic program as LLVM IR code to <basename>.ll'
    )
    args = parser.parse_args()

    try:
        program = load_program(args.program)
    except BasicSyntaxError as bse:
        print(F"{bse.message} in line {bse.line_number} of file.")
        # traceback.print_exc()
        sys.exit(1)
    except FileNotFoundError as f:
        print(F"File not found {f}")
        sys.exit(1)


    if args.llvm:
        executor = Executor(program)
        # Generate filename from input program name
        import os
        base_name = os.path.splitext(args.program)[0]
        filename = f"{base_name}.ll"
        ir_code = generate_llvm_ir(program)
        with open(filename, "w") as f:
            f.write(ir_code)
        print(f"LLVM IR saved to {filename}")
        sys.exit(0)

    if args.trace:
        with open("tracefile.txt", "w") as f:
            executor = Executor(program, trace_file=f)
            rc = executor.run_program()
    else:
        executor = Executor(program)
        rc = executor.run_program()
    print(F"Program completed with a status of {rc}")

    if args.symbols:
        pprint.pprint(executor._symbols.dump())

    if rc in [RunStatus.END_OF_PROGRAM, RunStatus.END_CMD]:
        sys.exit(0)
    if rc == RunStatus.END_STOP:
        sys.exit(1)
    sys.exit(2)
