"""
Main program for runningebugging a basic program.
"""
import sys
import pprint
import argparse

from basic_types import UndefinedSymbol, BasicSyntaxError

from basic_interpreter import load_program, Executor, eval_expression


class BasicShell:
    def __init__(self, program_file):
        self._program_file = program_file
        self.executor = None
        self.load()
        self._breakpoints = []
        self._data_breakpoints = []

    def load(self):
        program = load_program(self._program_file)
        executor = Executor(program)
        self.executor = executor

    def usage(self, cmd):
        """
        Print usage for one command.
        :param cmd:
        :return:
        """
        tup = self.commands[cmd]
        usage = tup[1]
        print(usage)

    def cmd_load(self, args):
        if args is not None:
            self._program_file = args
        print("Loading ", self._program_file)
        self.load()

    def print_current(self, args):
        line = self.executor.get_current_line()
        print(line.source)

    def cmd_list(self, args):
        count = 10
        if args:
            args = args.split()
            args = [arg.strip() for arg in args]
            if not str.isdigit(args[0]):
                print(F"Invalid line number {args[0]}")
                self.usage("list")
                return
            start_line_number = int(args[0])
            try:
                cl = self.executor._find_line(start_line_number)
            except BasicSyntaxError as e:
                print("Line number not found.")
                return
            index = cl.index

            if len(args) > 1:
                if not str.isdigit(args[1]):
                    print(F"Invalid count {args[1]}")
                    self.usage("list")
                    return
                count = int(args[1])
        else:
            index = self.executor._index
        for i in range(count):
            if index >= len(self.executor._program):
                break
            program_line = self.executor._program[index]
            print(program_line.source)
            index = program_line.next

    def format_cl(self, cl):
        program_line = self.executor._program[cl.index]
        offset = cl.offset
        return F"Line: {program_line.line:6}: Clause: {offset}"


    def cmd_for_stack(self, args):
        """
        Dumps the for/next stack, so you can see if you are in any loops.
        :param args: Not used.
        :return:
        """
        count = 10
        index = self.executor._index
        print("For/next stack:")
        if len(self.executor._for_stack) == 0:
            print("\t<empty>")
        for for_record in self.executor._for_stack:
            print("\t", for_record)

    def cmd_gosub_stack(self, args):
        """
        Dumps the gosub stack, so you can see if you are in any loops.
        :param args: Not used.
        :return:
        """
        index = self.executor._index
        print("GOSUB stack:")
        if len(self.executor._gosub_stack) == 0:
            print("\t<empty>")
        for cl in self.executor._gosub_stack:
            print("\t", self.format_cl(cl))

    def cmd_quit(self, args):
        sys.exit(0)

    def cmd_symbols(self, args):
        if args:
            try:
                pprint.pprint(self.executor.get_symbol(args))
                pprint.pprint(self.executor.get_symbol_type(args))
            except UndefinedSymbol as us:
                print(F"The symbol '{args}' is not defined.")
        else:
            pprint.pprint(self.executor._symbols.dump())

    def cmd_print(self, args):
        if not args:
            self.usage("?")
            return

        try:
            result = eval_expression(self.executor._symbols, args)
        except:
            print("Invalid expression")
            return
        print(result)


    def cmd_next(self, args):
        """
        Executes one program line, or until a control transfer. A NEXT from a FOR loop does a control
        transfer each time.
        :param args:  Not used.
        :return: Noneblist
        """
        self.print_current("")
        self.executor.execute_current_line()

    def cmd_run(self, args):
        rc = self.executor.run_program(self._breakpoints, self._data_breakpoints)
        if rc == 1:
            print("Breakpoint!")
            self.print_current(None)
        elif rc == 2:
            print(F"Data Breakpoint before line {self.executor._program[self.executor._index].line} {self.executor._statement_offset}")
            self.print_current(None)
        else:
            print("Program completed.")

    def cmd_break(self, args):
        """
        set a breakpoint. Breakpoints happen after the current LINE completes.
        A data breakpoint stops execution AFTER the access is done.
        :param args:
        :return:
        """
        if args == "clear":
            self._breakpoints = []
            self._data_breakpoints = []
            return

        if args == "list" or args == None:
            print("Breakpoints:")
            for i in self._breakpoints:
                print("\t", i)
            print("Data breakpoints:")
            for i in self._data_breakpoints:
                print("\t", i)
            return

        if str.isdigit(args):
            self._breakpoints.append(int(args))
            print("Added breakpoint at line ", args)
        else:
            self._data_breakpoints.append(args)
            print("Added data breakpoint at line ", args)

    def cmd_help(self, args):
        print("Commands are:")
        for key in self.commands:
            tup = self.commands[key]
            print(F"\t{key}: {tup[1]}")

    commands = {
        "break": (cmd_break, "Usage: break LINE or break SYMBOL or break list break clear"),
        "forstack": (cmd_for_stack, "Usage: fors"),
        "gosubs": (cmd_gosub_stack, "Usage: gosubs"),
        "help": (cmd_help, "Usage: help"),
        "load": (cmd_load, "Usage: load <program>"),
        "list": (cmd_list, "Usage: list start count"),
        "quit": (cmd_quit, "Usage: quit"),
        "run": (cmd_run, "Usage: run"),
        "next": (cmd_next, "Usage: next"),
        "sym": (cmd_symbols, "Usage: sym <symbol>"),
        "?": (cmd_print, "Usage: ? expression"),
    }

    def find_command(self, prefix):
        matches = [cmd for cmd in self.commands if cmd.startswith(prefix)]
        if len(matches) == 1:
            return matches[0]
        return None

    def do_command(self):
        while True:
            print("> ", end='')
            cmd_line = input()

            # Make ?A$ work, not just ? A$
            if cmd_line.startswith("?") and len(cmd_line) > 1 and cmd_line[1] != ' ':
                cmd_line = "? " + cmd_line[1:]

            info = cmd_line.split(" ", 1)
            cmd = info[0]
            # Make ?A$ work, not just ? A$
            if cmd.startswith("?") and len(cmd) > 1 and cmd[1] != ' ':
                cmd = "? " + cmd[1:]

            if len(info) > 1:
                args = info[1]
            else:
                args = None
            match = self.find_command(cmd)
            if match:
                cmd = match
            if cmd not in self.commands:
                print(F"Unknown command {cmd}")
                self.cmd_help(args)
                continue
            tup = self.commands[cmd]
            function = tup[0]
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
    debugger = BasicShell(args.program)
    debugger.do_command()