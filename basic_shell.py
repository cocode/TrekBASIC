"""
Main program for running a BASIC program.

Commands can be abbreviated to the minimum unique substring.
Commonly used commands should be one letter, if possible.
c - continue
n - next
s - step

"""
import os
import sys
import pprint
import argparse
import time
import traceback

from basic_types import UndefinedSymbol, BasicSyntaxError, SymbolType, ProgramLine

from basic_interpreter import Executor
from basic_loading import load_program, tokenize
from basic_statements import eval_expression
from basic_types import RunStatus
from llvm.codegen import generate_llvm_ir


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
    def __init__(self, program_file=None):
        self._program_file = program_file
        self.executor = None
        # TODO Investigate better failure handling
        self.load_status = False
        if self._program_file:
            self.load_from_file()
        self._breakpoints = []
        self._data_breakpoints = []
        self._coverage = None

    def load_from_string(self, listing):
        """
        Used by test code
        :return:
        """
        # TODO Do I need better error handling here?
        program = tokenize(listing)
        executor = Executor(program)
        self.executor = executor

    def load_program(self, program):
        """
        Used by renum code to replace source program with renumbered one
        :return:
        """
        # TODO Do I need better error handling here?
        executor = Executor(program)
        self.executor = executor

    def load_from_file(self, coverage:bool=False) -> None:
        self.load_status = False

        if not os.path.exists(self._program_file):
            if os.path.exists(self._program_file+".bas"):
                self._program_file += ".bas"

        if not os.path.exists(self._program_file):
            print("File not found: " + self._program_file)
            return

        print("Loading ", self._program_file)
        # TODO Clean up handling load failures. This is a quick hack.
        try:
            program = load_program(self._program_file)
        except FileNotFoundError as e:
            print(F"File {self._program_file} not found.")
            return
        except BasicSyntaxError:
            return
        except Exception as e:
            print(e)
            traceback.print_exc()
            return
        executor = Executor(program, coverage=coverage)
        self.executor = executor
        self.load_status = True
        return

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
        self.load_from_file()

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

    def cmd_save(self, args):
        if args is None:
            print("Save needs a file name.")
            return
        filename = args.strip()
        if not filename.endswith(".bas"):
            filename += ".bas"

        if os.path.exists(filename):
            print("No overwriting of files supported now. Still debugging. Save it to new name.")
            return
        lines = self.executor.get_program_lines()
        with open(filename, "w") as f:
            for line in lines:
                print(line, file=f)
        print(F"Program saved as {filename}")



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
        self.load_from_file(coverage=coverage)
        self.cmd_continue(None)

    def cmd_benchmark(self, args):
        load_start = time.perf_counter()
        self.load_from_file(coverage=False)
        load_time = time.perf_counter() - load_start
        run_start = time.perf_counter()
        self.cmd_continue(None)
        run_time = time.perf_counter() - run_start
        # only noting "load time", as this had it: https://archive.org/details/byte-magazine-1981-09/page/n193/mode/2up
        print(F"Load time {load_time:10.3f} sec. Run time: {run_time:10.3f} sec.")

    def build_line_map(self, old_program, start_line, increment):
        st_count = 0
        line_map = {}
        cur_line = start_line
        for line in old_program:
            line_number = line.line
            line_map[line_number] = cur_line
            for statement in line.stmts:
                cur_line += increment
                st_count += 1
        return line_map, st_count

    def renumber(self, old_program, line_map, start_line, increment):
        new_program:ProgramLine = []
        cur_line = start_line
        for line in old_program:
            for statement in line.stmts:
                ps = statement.renumber(line_map)
                ps = ProgramLine(cur_line, [ps], len(new_program), str(cur_line)+" " + str(ps))
                new_program.append(ps)
                cur_line += increment
        return new_program

    def format(self, old_program):
        """
        Parses the program, and returns the new program. this should standardize formatting, spacing.
        :param old_program:
        :return:
        """
        new_program:ProgramLine = []
        # Make a dummy, identity map. We are renumbering to the same numbers.
        line_map = {line.line:line.line for line in old_program}
        for line in old_program:
            new_statements = []
            for statement in line.stmts:
                ps = statement.renumber(line_map)
                new_statements.append(ps)
            # TODO. The "next" from the last line should be -1
            string_statements = ":".join([str(stmt) for stmt in new_statements])
            program_line = ProgramLine(line.line, new_statements, len(new_program), str(line.line)+" " +
                                       str(string_statements))
            new_program.append(program_line)
        return new_program

    def cmd_format(self, args):
        """
        Canonically formats the program.
        Does a "renumber" to the same lines, cleaning up in the process.

        :param args: Nothing.
        :return:
        """

        old_program = self.executor._program
        new_program = self.format(old_program)
        self.load_program(new_program)
        print(F"Formatted {len(old_program)} lines to {len(new_program)} lines")



    def cmd_renum(self, args):
        """
        Renumber the program.
        Basic algorithm:
            1. Split lines to single statement lines
            2. Walk through once to build a map of old line numbers to new
            3. Create a new program from the old statements
            4. Renumber the statements, in place.

        :param args:
        :return:
        """
        # renum start_line, increment.
        # TODO maybe add a "split lines with multiple statements", or just always do it.
        if args == None:
            args = []
        else:
            args = args.split()
        if len(args) == 0:
            start_line = 100
        else:
            start_line = int(args[0])
        if len(args) > 1:
            increment = int(args[1])
        else:
            increment = 10

        print(F"Renumber starting with line {start_line}, with increment {increment}")
        old_program = self.executor._program

        new_program = []
        line_map, st_count = self.build_line_map(old_program, start_line, increment)
        new_program = self.renumber(old_program, line_map, start_line, increment)
        self.load_program(new_program)
        print(F"Renumbered {len(old_program)} lines, and {st_count} statements to {len(new_program)} lines")

    def cmd_llvm(self, args):
        """
        Generate LLVM IR for the loaded program.
        :param args: Optional filename to save the IR to.
        :return:
        """
        if not self.executor or not self.executor._program:
            print("No program loaded.")
            return

        ir_code = generate_llvm_ir(self.executor._program)

        if args:
            filename = args.strip()
            with open(filename, "w") as f:
                f.write(ir_code)
            print(f"LLVM IR saved to {filename}")
        else:
            print(ir_code)

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
        print("Commands can be abbreviated to shortest unique prefix.")
        print("For convenience, 'r' works for 'run', and 'c' for 'continue'")

    cmd_abrev = {
        # Abbreviations for commands that get typed a lot.
        "r": "run",
        "c": "continue",
    }
    commands = {
        "break": (cmd_break, "Usage: break LINE or break SYMBOL or break list break clear"+
                  "\n\t\tSets a breakpoint on a line, or on writes to a variable"+
                  "\n\t\tNote that if you have an array and a scale with the same"+
                  "\n\t\tname, it will break on writes to either one."),
        "continue": (cmd_continue, "Usage: continue\n\t\tContinues, after a breakpoint."),
        "forstack": (cmd_for_stack, "Usage: fors\n\t\tPrints the FOR stack."),
        "format": (cmd_format, "Usage: format\n\t\tFormats the program. Does not save it."),
        "gosubs": (cmd_gosub_stack, "Usage: gosubs\n\t\tPrints the FOR stack."),
        "help": (cmd_help, "Usage: help"),
        "load": (cmd_load, "Usage: load <program>\n\t\tRunning load clears coverage data."),
        "coverage": (cmd_koverage, "Usage: coverage\n\t\tPrint code coverage report."+
                     "\n\t\tkoverage on\n\t\tkoverage off\n\t\tkoverage clear\n\t\tkoverage report <save|load|list>"),
        "list": (cmd_list, "Usage: list start count"),
        "quit": (cmd_quit, "Usage: quit"),
        "renumber": (cmd_renum, "Usage: renum <start <increment>>\n\t\tRenumbers the program."),
        "run": (cmd_run, "Usage: run <coverage>\n\t\tRuns the program from the beginning."),
        "benchmark": (cmd_benchmark, "Usage: becnhmark\n\t\tRuns the program from the beginning, and shows timing."),
        "next": (cmd_next, "Usage: next"),
        "sym": (cmd_symbols, "Usage: sym <symbol> <type>"+
                "\n\t\tPrints the symbol table, or one entry."+
                "\n\t\tType is 'variable', 'array' or 'function'. Defaults to 'variable'."),
        "save": (cmd_save, "Usage: save FILE"+
                "\n\t\tSaves the current program to a new file."),
        "?": (cmd_print, "Usage: ? expression\n\t\tEvaluates and prints an expression."
              "\n\t\tNote: You can't print single array variables. Use 'sym'"),
        "llvm": (cmd_llvm, "llvm [file]: generate LLVM IR and print to console or save to file"),

    }

    def find_command(self, prefix):
        if prefix in self.cmd_abrev:
            prefix = self.cmd_abrev[prefix]

        matches = [cmd for cmd in self.commands if cmd.startswith(prefix)]
        if len(matches) == 1:
            return matches[0]
        return None

    def do_command(self):
        while True:
            print("> ", end='')
            try:
                cmd_line = input()
            except EOFError as e:
                sys.exit(0)

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
    parser.add_argument('program', nargs='?', help="The name of the basic file to run. Will add '.bas' of not found.")
    args = parser.parse_args()
    if len(sys.argv) > 1:
        print(F"Usage: python3 basic_shell.py name_of_program.bas")
        sys.exit(1)
    cmd = None
    debugger = BasicShell(args.program)
    debugger.do_command()