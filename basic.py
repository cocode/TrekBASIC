"""
Main program for running a basic program.
"""
import sys
import argparse
import pprint

from basic_interpreter import load_program, Executor

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run BASIC programs.')
    parser.add_argument('program', help="The name of the basic file to run. Will add '.bas' of not found.")
    parser.add_argument('--trace', '-t', action='store_true', help="Write  a trace of execution to 'tracefile.txt'.")
    parser.add_argument('--symbols', '-s', action='store_true', help="Dump the symbol table on exit.")
    args = parser.parse_args()
    # Makes it to 1320 of superstartrek, and line 20 of startrek.bas
    if len(sys.argv) < 2:
        print("Usage: python3 basic_intrpreter.py name_of_program.bas")
        sys.exit(1)
    program = load_program(args.program)
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
