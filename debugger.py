"""
Main program for debugging a basic program.
"""
import sys
import pprint
import argparse

from basic_utils import format_line


from basic_interpreter import load_program, Executor

class Command:
    def __init__(self, executor):
        self.executor = executor

    def cmd_print_current(self, args):
        line = self.executor.get_current_line()
        print(line.source)

    def cmd_quit(self, args):
        sys.exit(0)

    def cmd_symbols(self, args):
        pprint.pprint(executor._symbols.dump())

    def cmd_step(self, args):
        self.cmd_print_current("")
        executor.execute_current_line()

    def cmd_run(self, args):
        executor.run_program() # should start from current line.

    def cmd_help(self, args):
        print("Commands are:")
        for key in self.commands:
            print(F"\t{key}")

    commands = {
        "help": cmd_help,
        "line": cmd_print_current,
        "quit": cmd_quit,
        "run": cmd_run,
        "step": cmd_step,
        "sym": cmd_symbols,
    }

    def do_command(self):
        while True:
            print("> ", end='')
            cmd_line = input()
            info = cmd_line.split(" ", 1)
            cmd = info[0]
            if cmd not in self.commands:
                print(F"Uknown command {cmd}")
                self.cmd_help(info[0])
                continue
            print("Got command ", cmd)
            function = self.commands[cmd]
            function(self, info[0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run BASIC programs.')
    parser.add_argument('program', help="The name of the basic file to run. Will add '.bas' of not found.")
    args = parser.parse_args()
    # Makes it to 1320 of superstartrek, and line 20 of startrek.bas
    if len(sys.argv) < 2:
        print("Usage: python3 basic_intrpreter.py name_of_program.bas")
        sys.exit(1)
    program = load_program(args.program)
    executor = Executor(program)
    cmd = None
    debugger = Command(executor)
    debugger.do_command()