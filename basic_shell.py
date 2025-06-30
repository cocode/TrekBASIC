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

# Add readline for command history and line editing
try:
    import readline
except ImportError:
    readline = None  # Windows doesn't have readline by default

from basic_parsing import ParsedStatement, ParsedStatementIf, ParsedStatementThen
from basic_types import UndefinedSymbol, BasicSyntaxError, SymbolType, ProgramLine, BasicRuntimeError

from basic_interpreter import Executor
from basic_loading import load_program, tokenize, tokenize_line
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
        tup = self.commands[cmd]
        usage = tup[1]
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

        :param args: None, "load" or "save", "lines". Saving and loading allow you to do multiple runs, to see if you
        can get to 100% coverage.
        :return:
        """
        if not self.executor:
            print("No program loaded.")
            return
            
        cmds = ["save", "load", "lines"]
        if args is not None:
            if args not in cmds:
                self.usage("coverage")
                return

        coverage = self.executor._coverage
        if coverage is None:
            print("Coverage was not enabled for the last / current run.")
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
        program_line = self.executor._program[cl.index]
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
        if not self.executor:
            print("No program has been loaded yet.")
            return
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

    def renumber(self, old_program: list[ProgramLine], line_map: dict[int:int], start_line: int, increment: int):
        new_program: list[ProgramLine] = []
        cur_line = start_line
        for index, line in enumerate(old_program):
            stmts: list[ParsedStatement] = []
            for statement in line.stmts:
                ps = statement.renumber(line_map)
                stmts.append(ps)
            if index + 1 == len(old_program):
                next_line = None
            else:
                next_line = len(new_program)
            source = self.smart_join(stmts)
            pl = ProgramLine(cur_line, stmts, next_line, str(cur_line)+" " + source)
            new_program.append(pl)
            cur_line += increment

        return new_program

    def format(self, old_program):
        """
        Parses the program, and returns the new program. This should standardize formatting, spacing.
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

    def cmd_llvm(self, args):
        """
        Generate LLVM IR for the loaded program.
        :param args: Optional filename to save the IR to.
        :return:
        """
        if not self.executor or not self.executor._program:
            print("No program has been loaded yet.")
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
        if args is not None:
            if args in self.commands:
                key = args
                tup = self.commands[args]
                print(F"\t{key}: {tup[1]}")
            return
        print("Commands are:")
        for key in self.commands:
            tup = self.commands[key]
            print(F"\t{key}: {tup[1]}")
        print("Commands can be abbreviated to shortest unique prefix.")
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
            
        # Find and remove the line
        program = self.executor._program
        original_count = len(program)
        program = [line for line in program if line.line != line_number]
        
        if len(program) == original_count:
            print(f"Line {line_number} not found")
            return
            
        # Rebuild program with correct next pointers and reload
        self.rebuild_and_reload_program(program)
        print(f"Line {line_number} deleted")

    def insert_or_replace_line(self, new_line: ProgramLine):
        """
        Insert a new line or replace an existing line in the program
        :param new_line: The new ProgramLine to insert
        """
        if not self.executor:
            # Create empty program if none exists
            program = []
        else:
            program = self.executor._program.copy()
            
        # Find insertion point or replacement
        insertion_index = 0
        replaced = False
        
        for i, existing_line in enumerate(program):
            if existing_line.line == new_line.line:
                # Replace existing line
                program[i] = new_line
                replaced = True
                break
            elif existing_line.line > new_line.line:
                # Insert before this line
                insertion_index = i
                break
            insertion_index = i + 1
            
        if not replaced:
            # Insert new line at correct position
            program.insert(insertion_index, new_line)
            
        # Rebuild program with correct next pointers and reload
        self.rebuild_and_reload_program(program)
        
        action = "replaced" if replaced else "inserted"
        print(f"Line {new_line.line} {action}")

    def rebuild_and_reload_program(self, program_lines: list[ProgramLine]):
        """
        Rebuild a program with correct next pointers and reload the executor
        :param program_lines: List of ProgramLine objects in correct order
        """
        # Set up next pointers correctly
        rebuilt_program = []
        for i, line in enumerate(program_lines):
            if i == len(program_lines) - 1:
                next_index = None  # Last line points to None
            else:
                next_index = i + 1
                
            rebuilt_line = ProgramLine(
                line.line,
                line.stmts,
                next_index,
                line.source
            )
            rebuilt_program.append(rebuilt_line)
            
        # Create new executor with the updated program  
        # This resets execution state as requested
        try:
            self.executor = Executor(rebuilt_program)
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
    commands = {
        "?": (cmd_print, "Usage: ? expression\n\t\tEvaluates and prints an expression."
              "\n\t\tNote: You can't print single array variables. Use 'sym'"),
        "benchmark": (cmd_benchmark, "Usage: benchmark\n\t\tRuns the program from the beginning, and shows timing."),
        "break": (cmd_break, "Usage: break LINE or break SYMBOL or break list break clear"+
                  "\n\t\tSets a breakpoint on a line, or on writes to a variable"+
                  "\n\t\tNote that if you have an array and a symbol with the same"+
                  "\n\t\tname, it will break on writes to either one."),
        "clear": (cmd_clear, "Usage: clear\n\t\tClears the current program and all state (breakpoints, watchpoints, coverage, etc.)"),
        "continue": (cmd_continue, "Usage: continue\n\t\tContinues, after a breakpoint."),
        "coverage": (cmd_coverage, "Usage: coverage\n\t\tPrint code coverage report."+
                     "\n\t\tkoverage on\n\t\tkoverage off\n\t\tkoverage clear\n\t\tkoverage report <save|load|list>"),
        "exit": (cmd_quit, "Usage: quit. Synonym for 'quit'"),
        "format": (cmd_format, "Usage: format\n\t\tFormats the program. Does not save it."),
        "forstack": (cmd_for_stack, "Usage: fors\n\t\tPrints the FOR stack."),
        "gosubs": (cmd_gosub_stack, "Usage: gosubs\n\t\tPrints the FOR stack."),
        "help": (cmd_help, "Usage: help <command>"),
        "list": (cmd_list, "Usage: list <start line number> <count>"),
        "llvm": (cmd_llvm, "llvm [file]: generate LLVM IR and print to console or save to file"),
        "load": (cmd_load, "Usage: load <program>\n\t\tRunning load clears coverage data."),
        "next": (cmd_next, "Usage: next.\n" +
                 "\t\tExecutes the next line of the program."),
        "quit": (cmd_quit, "Usage: quit. Synonym for 'exit'"),
        "renumber": (cmd_renum, "Usage: renum <start <increment>>\n\t\tRenumbers the program."),
        "run": (cmd_run, "Usage: run <coverage>\n\t\tRuns the program from the beginning.\n""+"
                         "\t\tAdding the string 'coverage' will cause code coverage data to be recorded from this run"),
        "save": (cmd_save, "Usage: save FILE"+
                "\n\t\tSaves the current program to a new file."),
        "statements": (cmd_stmts, "Usage: stmt <line>\n\t\tPrints the tokenized version of the program." +
                 "\n\t\tThis is used for debugging TrekBasic."),
        "symbols": (cmd_symbols, "Usage: sym <symbol> <type>"+
                "\n\t\tPrints the symbol table, or one entry."+
                "\n\t\tType is 'variable', 'array' or 'function'. Defaults to 'variable'."+
                "\n\t\tThis is used for debugging TrekBask."),
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
            tup = self.commands[cmd]
            function = tup[0]
            function(self, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run BASIC programs.')
    parser.add_argument('program', nargs='?', help="The name of the basic file to run. Will add '.bas' of not found.")
    args = parser.parse_args()
    cmd = None
    debugger = BasicShell(args.program)
    debugger.do_command()
    print("TrekBasic: Done")