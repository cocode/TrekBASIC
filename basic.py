"""
Main program for running a basic program from the command line.
"""
import os
import sys
import argparse
import pprint
import time

from basic_interpreter import Executor
from basic_loading import load_program
from basic_types import BasicSyntaxError, RunStatus
from basic_utils import TRACE_FILE_NAME

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run BASIC programs.')
    parser.add_argument('program', help="The name of the basic file to run. Will add '.bas' of not found.")
    parser.add_argument('--trace', '-t', action='store_true', help="Write  a trace of execution to 'tracefile.txt'.")
    parser.add_argument('--symbols', '-s', action='store_true', help="Dump the symbol table on exit.")
    parser.add_argument('--time', action='store_true', help="Time the execution (excluding parsing/loading).")
    args = parser.parse_args()
    if not os.path.exists(args.program):
        if os.path.exists(args.program+".bas"):
            args.program = args.program+".bas"
    try:
        program = load_program(args.program)
    except BasicSyntaxError as bse:
        print(F"{bse.message} in line {bse.line_number} of file.")
        sys.exit(1)
    except FileNotFoundError as f:
        print(F"File not found {f}")
        sys.exit(1)
    except ValueError as f:
        print(F"Value Error {f}")
        sys.exit(1)

    if args.trace:
        with open(TRACE_FILE_NAME, "w") as f:
            executor = Executor(program, trace_file=f)
            if args.time:
                start_time = time.time()
            rc = executor.run_program()
            if args.time:
                end_time = time.time()
                execution_time = end_time - start_time
                print(f"Execution time: {execution_time:.5f} seconds")
    else:
        executor = Executor(program)
        if args.time:
            start_time = time.time()

        try:
            rc = executor.run_program()
        except BasicSyntaxError as rte:
            print(F"{rte.message} in line {rte.line_number} of file.")
            sys.exit(1)

        if args.time:
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Execution time: {execution_time:.5f} seconds")
    print(F"Program completed with a status of {rc}")

    if args.symbols:
        pprint.pprint(executor._symbols.dump())

    if rc in [RunStatus.END_OF_PROGRAM, RunStatus.END_CMD]:
        sys.exit(0)
    if rc == RunStatus.END_STOP:
        sys.exit(1)
    sys.exit(2)
