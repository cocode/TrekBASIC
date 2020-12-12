"""
Main program for running a BASIC program.

Commands can be abbreviated to the minimum unique substring.
Commonly used commands should be one letter, if possible.
c - continue
n - next
s - step

"""
import sys
import pprint
import argparse
import time

from basic_types import UndefinedSymbol, BasicSyntaxError, SymbolType

from basic_interpreter import Executor, ControlLocation
from basic_loading import load_program
from basic_statements import eval_expression
from basic_types import RunStatus


def print_coverage_report(coverage, program, lines):
    total_lines = len(program)
    total_stmts = 0
    for p in program:
        total_stmts += len(p.stmts)

    if total_stmts == 0:
        print("Program is empty.")
        return

    executed_lines = len(coverage)
    executed_stmts = 0
    for s in coverage.values():
        executed_stmts += len(s)
    column = 20
    print(F'{"Total":>{column}} {"Executed":>{column}} {"Percent":>{column}}')
    print(F"{total_lines:{column}} {executed_lines:{column}} {100 * executed_lines / total_lines:{column}.1f}%")
    print(F"{total_stmts:{column}} {executed_stmts:{column}} {100 * executed_stmts / total_stmts:{column}.1f}%")
    # To start with, just print LINEs that have not been executed at all. Later we can get to statements.
    if lines:
        for l in program:
            if l.line not in coverage:
                slist = [i for i, j in enumerate(l.stmts)]
                print(F"{l.line}: {slist}")
            else:
                # Line has had SOME of its statements executed.
                slist = [i for i, j in enumerate(l.stmts)]
                left = [i for i, j in enumerate(l.stmts) if i not in coverage[l.line]]
                if len(left) != 0:
                    print(F"{l.line}: {left} of {slist}")


class BasicShell:
    def __init__(self, program_file):
        self._program_file = program_file
        self.executor = None
        self.load()
        self._breakpoints = []
        self._data_breakpoints = []
        self._coverage = None

    def load(self, coverage=False):
        print("Loading ", self._program_file)
        program = load_program(self._program_file)
        executor = Executor(program, coverage=coverage)
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
        self.load()

    def cmd_koverage(self, args):
        """
        Reports on code coverage.
        Called coverage because we want "continue" to be a single character command.
        I'd name it "coverage", but I don't want to conflict with "continue"

        :param args: None, "load" or "save", "lines". Saving and loading allow you to do multiple runs, to see if you
        can get to 100% coverage.
        :return:
        """
        cmds = ["on", "off", "save", "load", "lines"]
        if args is not None:
            if args not in cmds:
                self.usage("coverage")
                return

        coverage = self.executor._coverage
        if coverage is None:
            print("Coverage was not enabled for the last / current run.")
        print_coverage_report(self.executor._coverage, self.executor._program, args=='lines')


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
                cl = self.executor.find_line(start_line_number)
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
            index = self.executor.get_current_index()
            if index is None:
                # Program has finished running.
                index = 0
        lines = self.executor.get_program_lines(index, count)
        for line in lines:
            print(line)

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
        print("GOSUB stack:")
        if len(self.executor._gosub_stack) == 0:
            print("\t<empty>")
        for cl in self.executor._gosub_stack:
            print("\t", self.format_cl(cl))

    def cmd_quit(self, args):
        sys.exit(0)

    def cmd_symbols(self, args):
        if args is None:
            pprint.pprint(self.executor._symbols.dump())
            return

        args = args.split()
        if args:
            symbol_type = SymbolType.VARIABLE
            if len(args)>1:
                if args[1] == "array":
                    symbol_type = SymbolType.ARRAY
                elif args[1] == "function":
                    symbol_type = SymbolType.FUNCTION
                elif args[1] == "variable":
                    symbol_type = SymbolType.VARIABLE
            try:
                pprint.pprint(self.executor.get_symbol_value(args[0], symbol_type))
                pprint.pprint(self.executor.get_symbol_type(args[0], symbol_type))
            except UndefinedSymbol as us:
                print(F"The symbol '{args[0]}' is not defined as a {symbol_type}.")
                print(F"Types are 'variable', 'array' and 'function'. Default is 'variable'")

    def cmd_print(self, args):
        if not args:
            self.usage("?")
            return

        try:
            result = eval_expression(self.executor._symbols, args)
        except UndefinedSymbol as e:
            print(e.message)
            return
        except BasicSyntaxError as e:
            print(e.message)
            return
        except Exception as e:
            print("Exception: "+ e)
            return
        print(result)

    def cmd_next(self, args):
        """
        Executes one program line, or until a control transfer. A NEXT from a FOR loop does a control
        transfer each time.

        TODO: Right now, this steps ONE STATEMENT at a time, not one line
        :param args:  Not used.
        :return: None
        """
        self.print_current("")
        self.cmd_continue("step")

    def cmd_continue(self, args):
        """
        Continue execution of a program from its current location.
        :param args: if "step", then single steps the program one step.
        :return: None
        """
        single_step = False
        if args=="step":
            single_step = True

        rc = self.executor.run_program(self._breakpoints, self._data_breakpoints, single_step=single_step)
        if rc == RunStatus.BREAK_CODE:
            print("Breakpoint!")
            self.print_current(None)
        elif rc == RunStatus.BREAK_DATA:
            loc = self.executor.get_current_location()
            line = self.executor.get_current_line()
            print(F"Data Breakpoint before line {line.line} clause: {loc.offset}")
            self.print_current(None)
        else:
            print(F"Program completed with return of {rc}.")


    def cmd_run(self, args):
        coverage = False
        if args is not None and args=="coverage":
            coverage = True
        self.load(coverage=coverage)
        self.cmd_continue(None)

    def cmd_benchmark(self, args):
        load_start = time.perf_counter()
        self.load(coverage=False)
        load_time = time.perf_counter() - load_start
        run_start = time.perf_counter()
        self.cmd_continue(None)
        run_time = time.perf_counter() - run_start
        # only noting "load time", as this had it: https://archive.org/details/byte-magazine-1981-09/page/n193/mode/2up
        print(F"Load time {load_time:10.1f} sec. Run time: {run_time:10.1f} sec.")

    def cmd_break(self, args):
        """
        set a breakpoint. Breakpoints happen after the current LINE completes.
        A data breakpoint stops execution AFTER the access is done.

        TODO Add clause as optional. break 100 2
        TODO Add read access breakpoints.
        :param args:
        :return:
        """
        if args == "clear":
            self._breakpoints = []
            self._data_breakpoints = []
            return

        if args == "list" or args == None:
            if self._breakpoints:
                print("Breakpoints:")
                for i in self._breakpoints:
                    print("\t", i)
            if self._data_breakpoints:
                print("Data breakpoints:")
                for i in self._data_breakpoints:
                    print("\t", i)
            return

        args = args.split()
        if len(args) == 0: # Got nothing but whitespace.
            self.usage("break")
            return
        if str.isdigit(args[0]):
            if len(args) == 1:
                offset = 0
            else:
                if not args[0].isdigit():
                    self.usage()
                    return
                offset = int(args[1])
            # Note this is not a ControlLocation, that's index, offset. We are working with line_number, offset
            breakpoint = (int(args[0]), offset)
            self._breakpoints.append(breakpoint)
            print("Added breakpoint at line: ", args, " clause: ", offset)
        else:
            self._data_breakpoints.append(args)
            print("Added data breakpoint at line ", args)

    def cmd_help(self, args):
        print("Commands are:")
        for key in self.commands:
            tup = self.commands[key]
            print(F"\t{key}: {tup[1]}")

    commands = {
        "break": (cmd_break, "Usage: break LINE or break SYMBOL or break list break clear"+
                  "\n\t\tSets a breakpoint on a line, or on writes to a variable"+
                  "\n\t\tNote that if you have an array and a scale with the same"+
                  "\n\t\tname, it will break on writes to either one."),
        "continue": (cmd_continue, "Usage: continue\n\t\tContinues, after a breakpoint."),
        "forstack": (cmd_for_stack, "Usage: fors\n\t\tPrints the FOR stack."),
        "gosubs": (cmd_gosub_stack, "Usage: gosubs\n\t\tPrints the FOR stack."),
        "help": (cmd_help, "Usage: help"),
        "load": (cmd_load, "Usage: load <program>\n\t\tRunning load clears coverage data."),
        "koverage": (cmd_koverage, "Usage: koverage\n\t\tPrint code coverage report."+
                     "\n\t\tkoverage on\n\t\tkoverage off\n\t\tkoverage clear\n\t\tkoverage report <save|load|list>"),
        "list": (cmd_list, "Usage: list start count"),
        "quit": (cmd_quit, "Usage: quit"),
        "run": (cmd_run, "Usage: run <coverage>\n\t\tRuns the program from the beginning."),
        "benchmark": (cmd_benchmark, "Usage: becnhmark\n\t\tRuns the program from the beginning, and shows timing."),
        "next": (cmd_next, "Usage: next"),
        "sym": (cmd_symbols, "Usage: sym <symbol> <type>"+
                "\n\t\tPrints the symbol table, or one entry."+
                "\n\t\tType is 'variable', 'array' or 'function'. Defaults to 'variable'."),
        "?": (cmd_print, "Usage: ? expression\n\t\tEvaluates and prints an expression."
              "\n\t\tNote: You can't print single array variables. Use 'sym'"),
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