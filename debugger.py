"""
Main program for debugging a basic program.
"""
import sys
import pprint
import argparse

from basic_types import UndefinedSymbol
from basic_utils import format_line


from basic_interpreter import load_program, Executor

class Command:
    def __init__(self, program_file):
        self._program_file = program_file
        self.executor = None
        self.load()
        self._breakpoints = []

    def load(self):
        program = load_program(self._program_file)
        executor = Executor(program)
        self.executor = executor

    def cmd_load(self, args):
        if args is not None:
            self._program_file = args
        print("Loading ", self._program_file)
        self.load()

    def cmd_print_current(self, args):
        line = self.executor.get_current_line()
        print(line.source)

    def cmd_quit(self, args):
        sys.exit(0)

    def cmd_symbols(self, args):
        pprint.pprint(self.executor._symbols.dump())

    def cmd_print(self, args):
        try:
            pprint.pprint(self.executor.get_symbol(args))
            pprint.pprint(self.executor.get_symbol_type(args))
        except UndefinedSymbol as us:
            print(F"The symbol '{args}' is not defined.")

    def cmd_step(self, args):
        self.cmd_print_current("")
        self.executor.execute_current_line()

    def cmd_run(self, args):
        rc = self.executor.run_program(self._breakpoints) # should start from current line.
        if rc == 1:
            print("Breakpoint!")
            self.cmd_print_current(None)
        else:
            print("Program completed.")

    def cmd_break(self, args):
        """
        set a breakpoint
        :param args:
        :return:
        """
        if args == "clear":
            self._breakpoints = []
            return

        if args == "list":
            print("Breakpoints:")
            for i in self._breakpoints:
                print("\t", i)
            return

        if args is None or not str.isdigit(args):
            print("Usage: break LINE or break list break clear")
            return
        self._breakpoints.append(int(args))
        print("Added breakpoint at line ", args)

    def cmd_help(self, args):
        print("Commands are:")
        for key in self.commands:
            print(F"\t{key}")

    commands = {
        "break": cmd_break,
        "help": cmd_help,
        "load": cmd_load,
        "line": cmd_print_current,
        "quit": cmd_quit,
        "run": cmd_run,
        "step": cmd_step,
        "sym": cmd_symbols,
        "?": cmd_print,
    }

    def do_command(self):
        while True:
            print("> ", end='')
            cmd_line = input()
            info = cmd_line.split(" ", 1)
            cmd = info[0]
            if len(info) > 1:
                args = info[1]
            else:
                args = None
            if cmd not in self.commands:
                print(F"Uknown command {cmd}")
                self.cmd_help(args)
                continue
            function = self.commands[cmd]
            function(self, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run BASIC programs.')
    parser.add_argument('program', help="The name of the basic file to run. Will add '.bas' of not found.")
    args = parser.parse_args()
    # Makes it to 1320 of superstartrek, and line 20 of startrek.bas
    if len(sys.argv) < 2:
        print("Usage: python3 basic_intrpreter.py name_of_program.bas")
        sys.exit(1)
    cmd = None
    debugger = Command(args.program)
    debugger.do_command()