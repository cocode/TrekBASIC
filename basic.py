"""
Main program for running a basic program from the command line.
"""
import os
import sys
import argparse
import pprint
import time
from typing import Optional, TextIO

from basic_interpreter import Executor
from basic_loading import load_program
from basic_types import BasicSyntaxError, RunStatus, Program
from basic_utils import TRACE_FILE_NAME

# Constants
BASIC_FILE_EXTENSION = ".bas"
EXIT_SUCCESS = 0
EXIT_STOP = 1
EXIT_ERROR = 2


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run BASIC programs.')
    parser.add_argument('program', help="The name of the basic file to run. Will add '.bas' of not found.")
    parser.add_argument('--trace', '-t', action='store_true', help="Write  a trace of execution to 'tracefile.txt'.")
    parser.add_argument('--symbols', '-s', action='store_true', help="Dump the symbol table on exit.")
    parser.add_argument('--time', action='store_true', help="Time the execution (excluding parsing/loading).")
    return parser.parse_args()


def find_program_file(program_name: str) -> str:
    """Find the program file, adding .bas extension if needed."""
    if os.path.exists(program_name):
        return program_name
    
    program_with_extension = program_name + BASIC_FILE_EXTENSION
    if os.path.exists(program_with_extension):
        return program_with_extension
    
    return program_name  # Return original name to trigger FileNotFoundError


def load_program_with_error_handling(program_path: str) -> Program:
    """Load a BASIC program with comprehensive error handling."""
    try:
        return load_program(program_path)
    except BasicSyntaxError as syntax_error:
        print(f"{syntax_error.message} in line {syntax_error.line_number} of file.")
        sys.exit(EXIT_ERROR)
    except FileNotFoundError as file_error:
        print(f"File not found {file_error}")
        sys.exit(EXIT_ERROR)
    except ValueError as value_error:
        print(f"Value Error {value_error}")
        sys.exit(EXIT_ERROR)


def execute_program(program: Program, trace_file: Optional[TextIO] = None, 
                   enable_timing: bool = False) -> tuple[RunStatus, Executor]:
    """Execute a BASIC program with optional tracing and timing."""
    executor = Executor(program, trace_file=trace_file)
    
    start_time = time.time() if enable_timing else None
    
    try:
        run_status = executor.run_program()
    except BasicSyntaxError as runtime_error:
        print(f"{runtime_error.message} in line {runtime_error.line_number} of file.")
        sys.exit(EXIT_ERROR)
    
    if enable_timing and start_time is not None:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time:.5f} seconds")
    
    return run_status, executor


def dump_symbol_table(executor: Executor) -> None:
    """Dump the symbol table to stdout."""
    pprint.pprint(executor._symbols.dump())


def determine_exit_code(run_status: RunStatus) -> int:
    """Determine the appropriate exit code based on run status."""
    if run_status in [RunStatus.END_OF_PROGRAM, RunStatus.END_CMD]:
        return EXIT_SUCCESS
    elif run_status == RunStatus.END_STOP:
        return EXIT_STOP
    else:
        return EXIT_ERROR


def main() -> None:
    """Main entry point for the BASIC interpreter."""
    args = parse_arguments()
    
    # Find and load the program
    program_path = find_program_file(args.program)
    program = load_program_with_error_handling(program_path)
    
    # Execute the program
    if args.trace:
        with open(TRACE_FILE_NAME, "w") as trace_file:
            run_status, executor = execute_program(program, trace_file=trace_file, enable_timing=args.time)
    else:
        run_status, executor = execute_program(program, enable_timing=args.time)
    
    print(f"Program completed with a status of {run_status}")
    
    # Dump symbols if requested
    if args.symbols:
        dump_symbol_table(executor)
    
    # Exit with appropriate code
    sys.exit(determine_exit_code(run_status))


if __name__ == "__main__":
    main()
