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
import re

from basic_reports import generate_html_coverage_report, print_coverage_report
from basic_symbols import SymbolTable

# Add readline for command history and line editing
try:
    import readline
except ImportError:
    readline = None  # Windows doesn't have readline by default

from basic_parsing import ParsedStatement, ParsedStatementIf, ParsedStatementThen
from basic_types import UndefinedSymbol, BasicSyntaxError, SymbolType, ProgramLine, Program, BasicRuntimeError

from basic_interpreter import Executor
from basic_loading import load_program, tokenize, tokenize_line
from basic_statements import eval_expression
from basic_types import RunStatus




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
        
        # Set up command history
        if readline:
            self.history_file = os.path.expanduser("~/.trekbasic_history")
            try:
                readline.read_history_file(self.history_file)
            except FileNotFoundError:
                pass  # No history file yet, that's fine
            except Exception:
                pass  # Ignore other readline errors
            
            # Set reasonable history length
            readline.set_history_length(1000)

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
        try:
            program = load_program(self._program_file)
        except BasicSyntaxError as e:
            print(F"{e} in line {e.line_number}")
            return

        try:
            executor = Executor(program, coverage=coverage)
        except BasicSyntaxError as e:
            print(F"{e} in line {e.line_number}")
            return
        self.executor = executor
        self.load_status = True
        return

    def usage(self, cmd):
        """
        Print usage for one command.
        :param cmd:
        :return:
        """
        function = self.commands[cmd]
        usage = self.cmd_help_map[function][0]
        print(usage)

    def cmd_load(self, filename):
        if filename is not None:
            if filename.startswith('"') and filename.endswith('"'):
                filename = filename[1:-1]
        if not os.path.exists(filename):
            if os.path.exists(filename + ".bas"):
                filename += ".bas"
            else:
                print("File not found: " + filename)
                return

        try:
            self._program_file = filename
            self.load_from_file()
        except BasicSyntaxError as bse:
            print(F"Syntax Error in line {bse.line_number}: {bse.message}")
            self._program_file = None


    def cmd_coverage(self, args):
        """
        Reports on code coverage. Code coverage is initiate by the "run coverage" command.
        Called coverage because we want "continue" to be a single character command.
        I'd name it "coverage", but I don't want to conflict with "continue"

        :param args: None, "load" or "save", "lines", "html". Saving and loading allow you to do multiple runs, to see if you
        can get to 100% coverage. "html" generates a beautiful HTML report.
        :return:
        """
        if not self.executor:
            print("No program loaded.")
            return
            
        cmds = ["save", "load", "lines", "html"]
        if args is not None:
            if args not in cmds:
                self.usage("coverage")
                return

        coverage = self.executor._coverage
        if coverage is None:
            print("Coverage was not enabled for the last / current run.")
            return
            
        if args == "html":
            generate_html_coverage_report(self.executor._coverage, self.executor._program, "coverage_report.html")
        else:
            print_coverage_report(self.executor._coverage, self.executor._program, args=='lines')


    def print_current(self, args):
        if not self.executor:
            print("No program has been loaded yet.")
            return
        line = self.executor.get_current_line()
        print(line.source)

    def cmd_list(self, args):
        count = 10
        if not self.executor or not self.executor._program:
            print("No program has been loaded yet.")
            return
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
                cl = self.executor._program[0]
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
        current_location =  self.executor.get_current_location()
        # Get the lines to list.
        lines = self.executor.get_program_lines(index, count)
        for local_line_offset, line in enumerate(lines):
            if local_line_offset + index == current_location.index:
                print("*",end="")
            else:
                print(" ", end="")
            print(line)

    def format_cl(self, cl):
        program_line = self.executor._program.get_line(cl.index)
        offset = cl.offset
        return F"Line: {program_line.line:6}: Clause: {offset}"


    def cmd_for_stack(self, args):
        """
        Dumps the for/next stack, so you can see if you are in any loops.
        :param args: Not used.
        :return:
        """
        if not self.executor:
            print("No program has been loaded yet.")
            return
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
        if not self.executor:
            print("No program has been loaded yet.")
            return
        print("GOSUB stack:")
        if len(self.executor._gosub_stack) == 0:
            print("\t<empty>")
        for cl in self.executor._gosub_stack:
            print("\t", self.format_cl(cl))

    def cmd_quit(self, args):
        # Save command history
        if readline:
            try:
                readline.write_history_file(self.history_file)
            except Exception:
                pass  # Ignore errors when saving history
        sys.exit(0)

    def cmd_clear(self, args):
        """
        Clear the current program and all state (breakpoints, watchpoints, coverage, etc.)
        """
        if self.executor:
            self.executor._close_trace_file_like()
            self.executor = None
        self._breakpoints = []
        self._data_breakpoints = []
        self._coverage = None
        self.load_status = False
        self._program_file = None
        print("Program and all state cleared")

    def cmd_save(self, args):
        if not self.executor:
            print("No program has been loaded yet.")
            return
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
        if not self.executor:
            print("No program has been loaded yet.")
            return

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
            if self.executor is None or self.executor._symbols is None:
                # This path can only do constant expresions, since there are no symbols.
                # this is what you get when using ? before running a program.
                symbols = SymbolTable()
            else:
                symbols = self.executor._symbols
            result = eval_expression(symbols, args)
        except UndefinedSymbol as e:
            print(e.message)
            return
        except BasicSyntaxError as e:
            print(e.message)
            return
        except TypeError as e:
            print("Type Exception: " + str(e))
            return
        except AttributeError as e:
            print("AttributeError: " + str(e))
            return
        except Exception as e:
            print("Exception: "+ str(e))
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
        # TODO Next from non-running state should run the program and run the first line.
        # But for now, print an error.
        if not self.executor._run in (RunStatus.RUN, RunStatus.BREAK_STEP):
            print("The program must be running, before you can single step.")
            print("You can use a breakpoint to get started.")
            # NOTE: The program starts in RUN mode, but after running once, its state is END, so
            # "n" after a program has terminated is the only case where this happens.
            return

        self.print_current("")
        self.cmd_continue("step")

    def cmd_continue(self, args):
        """
        Continue execution of a program from its current location.
        :param args: if "step", then single steps the program one step.
        :return: None
        """
        if not self.executor:
            print("No program has been loaded yet.")
            return
        single_step = False
        if args=="step":
            single_step = True

        try:
            rc = self.executor.run_program(self._breakpoints, self._data_breakpoints, single_step=single_step)
        except BasicRuntimeError as e:
            print("Runtime Error: ", e.message)
            return
        except BasicSyntaxError as e:
            print("Syntax Error: ", e.message)
            return
        if rc == RunStatus.BREAK_CODE:
            print("Breakpoint!")
            self.print_current(None)
        elif rc == RunStatus.BREAK_DATA:
            loc = self.executor.get_current_location()
            line = self.executor.get_current_line()
            print(F"Data Breakpoint before line {line.line} clause: {loc.offset}")
            self.print_current(None)
        elif rc == RunStatus.BREAK_STEP:
            print(F"Single Step Done {rc}.")
        else:
            print(F"Program completed with return of {rc}.")


    def cmd_run(self, args):
        if not self.executor:
            print("No program has been loaded yet.")
            return

        coverage = False
        if args is not None and args == "coverage":
            coverage = True

        # Extract program from current executor, then create fresh executor
        program = self.executor._program
        self.executor = Executor(program, coverage=coverage)
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
            cur_line += increment
            for statement in line.stmts:
                st_count += 1
        return line_map, st_count

    def smart_join(self, stmts: list[ParsedStatement]) -> str:
        """
        Joins statements back together, so we can reconstitute the source after renumbering.
        Note this produces canonically formatted code, not the original code. For example,
        100 A = 3 becomes 100 LET A=3
        """
        source = ""
        last_was_then = False  # TODO for ELSE?
        last_was_if = False  # TODO for ELSE?
        for stmt in stmts:
            if source:
                # Only add colons, after the first statement
                if not (last_was_then or last_was_if):
                    source += ":"
                else:
                    source += " "
            source += str(stmt)
            last_was_if = isinstance(stmt, ParsedStatementIf)
            last_was_then = isinstance(stmt, ParsedStatementThen)
        return source

    def renumber(self, old_program: Program, line_map: dict[int:int], start_line: int, increment: int):
        new_program_lines: list[ProgramLine] = []
        cur_line = start_line
        for index, line in enumerate(old_program):
            stmts: list[ParsedStatement] = []
            for statement in line.stmts:
                ps = statement.renumber(line_map)
                stmts.append(ps)
            source = self.smart_join(stmts)
            pl = ProgramLine(cur_line, stmts, str(cur_line)+" " + source)
            new_program_lines.append(pl)
            cur_line += increment

        return Program(new_program_lines)

    def format(self, old_program: Program):
        """
        Parses the program, and returns the new program. This should standardize formatting, spacing.
        :param old_program:
        :return:
        """
        new_program_lines: list[ProgramLine] = []
        # Make a dummy, identity map. We are renumbering to the same numbers.
        line_map = {line.line:line.line for line in old_program}
        for line in old_program:
            new_statements = []
            for statement in line.stmts:
                ps = statement.renumber(line_map)
                new_statements.append(ps)
            string_statements = ":".join([str(stmt) for stmt in new_statements])
            program_line = ProgramLine(line.line, new_statements, str(line.line)+" " +
                                       str(string_statements))
            new_program_lines.append(program_line)
        return Program(new_program_lines)

    def cmd_format(self, args):
        """
        Canonically formats the program.
        Does a "renumber" to the same lines, cleaning up in the process.

        :param args: Nothing.
        :return:
        """
        if not self.executor:
            print("No program has been loaded yet.")
            return

        old_program = self.executor._program
        new_program = self.format(old_program)
        self.load_program(new_program)
        print(F"Formatted {len(old_program)} lines to {len(new_program)} lines")

    def cmd_renum(self, args, verbose: bool = True):
        """
        Renumber the program.
        See cmd_format

        Basic algorithm:
            1. Walk through once to build a map of old line numbers to new
            2. Copy the program
            3. Walk the new program, calling renum, and passing the map.
            4. Each statement has a renum method that knows what to do for that statement.

        :param: args:
        :param: verbose: Normally true, off for testing.
        :return:
        """
        if not self.executor:
            print("No program has been loaded yet.")
            return
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

        if verbose:
            print(F"Renumber starting with line {start_line}, with increment {increment}")
        old_program = self.executor._program
        new_program = []
        line_map, st_count = self.build_line_map(old_program, start_line, increment)
        new_program = self.renumber(old_program, line_map, start_line, increment)
        self.load_program(new_program)
        if verbose:
            print(F"Renumbered {len(old_program)} lines, and {st_count} statements to {len(new_program)} lines")

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
        if args is not None:
            if args in self.commands:
                key = args
                function = self.commands[args]
                help_text, _ = self.cmd_help_map[function]
                lines = help_text.split('\n')
                print(f"\t{key}: {lines[0]}")
                pad = ' ' * (8 + len(key) + 1)
                for line in lines[1:]:
                    print(f"{pad}{line}")
            return
        print("General Commands:")
        self._print_help_group("general")
        print("\nDebug Commands:")
        print("\tDebug Command generally work while a program is running, or after it ends..")
        print("\tCommands like forstack and symbols require a program context to work.\n")
        self._print_help_group("debug")
        print("\nCommands can be abbreviated to shortest unique prefix.")
        print("For convenience, 'r' works for 'run', and 'c' for 'continue'")
        print()
        print("BASIC Line Entry:")
        print("\t<number> <statements> - Insert/replace program line")
        print("\t<number>              - Delete program line")
        print("\tExamples:")
        print("\t\t100 PRINT \"HELLO\"")
        print("\t\t200 FOR I=1 TO 10: PRINT I: NEXT I")
        print("\t\t100                  (deletes line 100)")
        print("\tLine numbers must be 1-65536")

    def _print_help_group(self, category):
        # Helper to print commands by category
        group_cmds = [k for k, fn in self.commands.items() if self.cmd_help_map[fn][1] == category]
        group_cmds.sort()
        if not group_cmds:
            return
        max_cmd_len = max(len(cmd) for cmd in group_cmds)
        for key in group_cmds:
            function = self.commands[key]
            help_text, _ = self.cmd_help_map[function]
            padding = " " * (max_cmd_len - len(key) + 1)
            lines = help_text.split('\n')
            print(f"\t{key}:{padding}{lines[0]}")
            pad = ' ' * (8 + len(key) + 1 + len(padding))
            for line in lines[1:]:
                print(f"{pad}{line}")

    def cmd_stmts(self, args):
        if not self.executor:
            print("No program has been loaded yet.")
            return

        if args:
            line_number = int(args.strip())
        else:
            line_number = None
        for line in self.executor._program:
            # If they give us a line number, only print that line's statements
            if line_number is not None and line_number != line.line:
                continue
            print(F"{line.line} ", end="")
            for statement in line.stmts:
                print(F"\t{statement}", end="|")
            print()

    def cmd_stop(self, args):
        if not self.executor:
            print("No program has been loaded yet.")
            return

        self.executor.restart()

    def handle_line_entry(self, line_input: str):
        """
        Handle entry of BASIC program lines (e.g., "100 PRINT A" or "100" to delete)
        :param line_input: The full line input (e.g., "100 PRINT A")
        """
        try:
            # Parse the line number and content
            parts = line_input.split(" ", 1)
            line_number = int(parts[0])
            
            # Validate line number range
            if line_number < 1 or line_number > 65536:
                print(f"Line number {line_number} out of range (1-65536)")
                return
                
            # Check if this is a delete operation (just line number, no content)
            if len(parts) == 1 or (len(parts) == 2 and parts[1].strip() == ""):
                self.delete_line(line_number)
                return
                
            # Parse the line using existing tokenizer
            try:
                new_program_line = tokenize_line(line_input)
            except BasicSyntaxError as e:
                print(f"Syntax error: {e.message}")
                return
                
            # Insert or replace the line in the program
            self.insert_or_replace_line(new_program_line)
            
        except ValueError:
            print("Invalid line number")
        except Exception as e:
            print(f"Error processing line: {e}")

    def delete_line(self, line_number: int):
        """
        Delete a line from the program
        :param line_number: Line number to delete
        """
        if not self.executor or not self.executor._program:
            print("No program has been loaded yet.")
            return
            
        # Use the Program class method to delete the line
        was_deleted = self.executor._program.delete_line(line_number)
        
        if not was_deleted:
            print(f"Line {line_number} not found")
            return
            
        print(f"Line {line_number} deleted")

    def insert_or_replace_line(self, new_line: ProgramLine):
        """
        Insert a new line or replace an existing line in the program
        :param new_line: The new ProgramLine to insert
        """
        if not self.executor:
            # Create empty program if none exists
            self.executor = Executor(Program([]))
            
        # Use the Program class method to insert or replace the line
        was_replaced = self.executor._program.insert_or_replace_line(new_line)
        self.executor.modified = True
        
        action = "replaced" if was_replaced else "inserted"
        print(f"Line {new_line.line} {action}")

    def rebuild_and_reload_program(self, program_lines: list[ProgramLine]):
        """
        Rebuild a program and reload the executor
        :param program_lines: List of ProgramLine objects in correct order
        """
        # Create new Program object and executor
        try:
            new_program = Program(program_lines)
            self.executor = Executor(new_program)
            # Mark as successfully loaded
            self.load_status = True
        except BasicSyntaxError as e:
            print(f"Error loading modified program: {e.message}")
            self.load_status = False


    cmd_abrev = {
        # Abbreviations for commands that get typed a lot.
        "r": "run",
        "c": "continue",
    }
    
    # Map from cmd_XXX method names to help text
    cmd_help_map = {
        cmd_print: (
            "Usage: ? expression"
            "\nEvaluates and prints an expression."
            "\nNote: You can't print single array variables. Use 'sym'"
            "\nYou may have wanted the 'help' command.",
            "general"
        ),
        cmd_benchmark: (
            "Usage: benchmark"
            "\nRuns the program from the beginning, and shows timing."
        ),
        cmd_break: (
            "Usage: break LINE or break SYMBOL or break list break clear"
            "\nSets a breakpoint on a line, or on writes to a variable"
            "\nNote that if you have an array and a symbol with the same name, it will break on writes to either one."
        ),
        cmd_clear: (
            "Usage: clear"
            "\nClears the current program and all state (breakpoints, watchpoints, coverage, etc.)"
            "\nSee also STOP command."
        ),
        cmd_continue: (
            "Usage: continue"
            "\nContinues, after a breakpoint."
        ),
        cmd_coverage: (
            "Usage: coverage [lines|html]"
            "\nPrint code coverage report."
            "\ncoverage lines - Show uncovered lines details"
            "\ncoverage html  - Generate beautiful HTML report"
            "\nNote: Coverage must be enabled with 'run coverage' first"
        ),
        cmd_quit: "Usage: quit. Synonym for 'exit'",
        cmd_format: (
            "Usage: format"
            "\nFormats the program. Does not save it."
        ),
        cmd_for_stack: (
            "Usage: fors"
            "\nPrints the FOR stack."
        ),
        cmd_gosub_stack: (
            "Usage: gosubs"
            "\nPrints the GOSUB stack."
        ),
        cmd_help: "Usage: help <command>",
        cmd_list: "Usage: list <start line number> <count>",
        cmd_load: (
            "Usage: load <program>"
            "\nRunning load clears coverage data."
        ),
        cmd_next: (
            "Usage: next."
            "\nExecutes the next line of the program."
        ),
        cmd_renum: (
            "Usage: renum <start <increment>>"
            "\nRenumbers the program."
        ),
        cmd_run: (
            "Usage: run <coverage>"
            "\nRuns the program from the beginning."
            "\nAdding the string 'coverage' will cause code coverage data to be recorded from this run"
        ),
        cmd_save: (
            "Usage: save FILE"
            "\nSaves the current program to a new file."
        ),
        cmd_stmts: (
            "Usage: stmt <line>"
            "\nPrints the tokenized version of the program."
            "\nThis is used for debugging TrekBasic."
        ),
        cmd_stop: (
            "Usage: stop."
            "\nIf you are running a program, this sets you back to the start."
            "\nUnlike clear, which clears the program, breakpoints, etc. This only resets execution."
        ),
        cmd_symbols: (
            "Usage: sym <symbol> <type>"
            "\nPrints the symbol table, or one entry."
            "\nType is 'variable', 'array' or 'function'. Defaults to 'variable'."
            "\nThis is used for debugging TrekBask."
        ),
    }

    # Add category flags programmatically so we don't have to edit every entry by hand
    _debug_cmds_set = {cmd_break, cmd_for_stack, cmd_gosub_stack, cmd_coverage, cmd_stmts, cmd_symbols}
    for _func, _val in list(cmd_help_map.items()):
        # If already tuple with 2 elements, assume it's (text, category) and skip
        if isinstance(_val, tuple) and len(_val) == 2:
            continue
        # Extract help text (might be tuple of one element or string)
        if isinstance(_val, tuple):
            _text = _val[0]
        else:
            _text = _val
        _cat = "debug" if _func in _debug_cmds_set else "general"
        cmd_help_map[_func] = (_text, _cat)

    commands = {
        "?": cmd_print,
        "benchmark": cmd_benchmark,
        "break": cmd_break,
        "clear": cmd_clear,
        "continue": cmd_continue,
        "coverage": cmd_coverage,
        "exit": cmd_quit,
        "format": cmd_format,
        "forstack": cmd_for_stack,
        "gosubs": cmd_gosub_stack,
        "help": cmd_help,
        "list": cmd_list,
        "load": cmd_load,
        "next": cmd_next,
        "quit": cmd_quit,
        "renumber": cmd_renum,
        "run": cmd_run,
        "save": cmd_save,
        "statements": cmd_stmts,
        "stop": cmd_stop,
        "symbols": cmd_symbols,
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

            # Check if this is a BASIC line entry (starts with digits followed by space)
            if re.match(r'^\d+(\s|$)', cmd_line):
                self.handle_line_entry(cmd_line)
                continue

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
            function = self.commands[cmd]
            function(self, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run BASIC programs.')
    parser.add_argument('program', nargs='?', help="The name of the basic file to run. Will add '.bas' of not found.")
    args = parser.parse_args()
    cmd = None
    debugger = BasicShell(args.program)
    debugger.do_command()
    print("TrekBasic: Done")