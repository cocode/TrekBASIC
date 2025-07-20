"""
This module contains the class, Executor, that runs BASIC programs
"""
from collections import namedtuple, defaultdict
import random
from typing import Optional, TextIO, List, Tuple, Dict, Set, Any, Union

import basic_functions
from basic_parsing import ParsedStatementElse
from basic_types import ProgramLine, Program, BasicInternalError, assert_syntax, BasicSyntaxError
from basic_types import SymbolType, RunStatus, BasicRuntimeError, ControlLocation
from basic_symbols import SymbolTable
from basic_utils import TRACE_FILE_NAME


# Target of a control transfer. Used by GOTO, GOSUB, NEXT, etc.
# TODO This should be a mutable class, and we should use it for the current instruction
# index: The index into the Executor._program list
# offset: The index into the Executor._program[x].stmts list.


# var: the index variable
# stop: The ending value, and expression
# step: The step, and expression. both expressions can change during loop execution
# stmt: Used to tell if we are initializing the loop, or looping. Don't think this is used now.
# Note: we don't need to save "start" it's only used on setup.
ForRecord = namedtuple("ForRecord", "var stop step stmt")


class Executor:
    def restart(self) -> None:
        self._location = ControlLocation(0,0)
        self._goto = None
        self._gosub_stack = []
        self._for_stack = []
        # Reset DATA/READ state
        self._data_position = None

    def __init__(self,
                 program: Program,
                 trace_file: Optional[TextIO] = None, 
                 stack_trace: bool = False,
                 coverage: Union[bool, Dict[int, Set[int]]] = False,
                 record_inputs: bool = False) -> None:
        """

        :param program:
        :param trace_file: Save a list of lines executed to a file for debugging
        :param record_inputs: TBD Record a list of lines entered by the user. Used for building test scripts.
        :param stack_trace: Rethrow BasicSyntaxErrors, so we get a stack trace.
        :param coverage: None, or a dict of (line_number:set of statements). Set to [] to enable coverage. Set to
        a coverage from a previous run, to add to that run
        """
        self._program: Program = program
        self._location: ControlLocation = ControlLocation(0,0)
        self._run: RunStatus = RunStatus.RUN
        # A "File-like" object. Could be File pointer - it's not the file name.
        self._trace_file_like: Optional[TextIO] = trace_file
        self._stack_trace: bool = stack_trace
        self._goto: Optional[ControlLocation] = None
        self._gosub_stack: List[ControlLocation] = []
        self._for_stack: List[ForRecord] = []
        # PyCharm complains if these are defined anywhere outside of __init__
        self._internal_symbols: Optional[SymbolTable] = None
        self._symbols: Optional[SymbolTable] = None
        self._data_breakpoints: List[str] = []
        # DATA/READ/RESTORE state  
        self._data_position: Optional[Tuple[int, int, int]] = None  # Current position: (line_index, stmt_index, value_index) or None for start
        self._coverage: Optional[Dict[int, Set[int]]] = defaultdict(set) if coverage else None
        if self._coverage:
            print("Running with code coverage")
        self.init_symbols()
        self.setup_program()
        self.modified: bool = False

    def init_symbols(self) -> None:
        self._internal_symbols = SymbolTable()
        self._symbols = self._internal_symbols.get_nested_scope()

    def set_trace_file(self, filepointer: Optional[TextIO]) -> None:
        self._trace_file_like = filepointer

    def _close_trace_file_like(self) -> None:
        if self._trace_file_like and hasattr(self._trace_file_like, 'close'):
            try:
                self._trace_file_like.close()
                self._trace_file_like = None
            except Exception:
                print(F"Failed to close trace file.")

    def setup_program(self) -> None:
        functions = basic_functions.PredefinedFunctions()
        for f in functions.functions:
            self._internal_symbols.put_symbol(f, "⌊", SymbolType.FUNCTION, arg=None)

        random.seed(1)

    def has_program(self) -> bool:
        return self._program is not None

    def program_len(self) -> int:
        return self._program.get_len()

    def run_program(self, breaklist: Optional[List[Tuple[int, int]]] = None,
                   data_breakpoints: Optional[List[str]] = None, 
                   single_step: bool = False) -> RunStatus:
        """
        Run the program. This can also be called to resume after a breakpoint.

        Data breakpoints happen AFTER the statement containing the access has completed.
        It would require substantial overhead to break BEFORE the statement, but it was
        almost free to break after.
        Since data breakpoints happen after the statement has completed, we also have to
        allow control transfers for the statement to happen, like going to the next line,
        otherwise the line would execute again when continuing.

        :param breaklist: A list of tuple - (program line numbers, clause) to break before.
        :param data_breakpoints: A list of str - Variables to break AFTER they are WRITTEN. (not read)
        :param single_step: If True, run one statement (not line) and then return
        :return: A value from RunStatus
        """
        if breaklist is None:
            breaklist: List[Tuple[int, int]] = []
        if data_breakpoints is None:
            data_breakpoints: List[str] = []
        self._run = RunStatus.RUN  # TODO Try finally on RunStatus?
        self._data_breakpoints = data_breakpoints
        if self._trace_file_like is None:
            with open(TRACE_FILE_NAME, "w") as f:
                pass   # just truncating the file, with the open.
        while True:
            if self.at_end():
                self._run = RunStatus.END_OF_PROGRAM
                return self._run

            current: ProgramLine = self.get_current_line()
            index: int = self.get_current_index()
            # If single step mode, allow them to go over the breakpoint they just hit.
            if not single_step:
                for breakpoint in breaklist:
                    if current.line == breakpoint[0]:
                        if self._location.offset == breakpoint[1]:
                            self._run = RunStatus.BREAK_CODE

            if self._run != RunStatus.RUN:
                return self._run

            if self._trace_file_like and self._location.offset == 0:
                print(F">{current.source}", file=self._trace_file_like)

            s = self.get_current_stmt()

            if self._trace_file_like:
                print(F"\t{s}", file=self._trace_file_like)

            execution_function = s.keyword.value.get_exec()
            try:
                execution_function(self, s)
            except BasicSyntaxError as bse:
                # TODO: This needs a bit more thought. The tests are checking for exceptions,
                # TODO and don't need the print statement. The user just needs the message printed.
                self._run = RunStatus.END_ERROR_SYNTAX
                raise BasicSyntaxError(bse.message, current.line) from bse
                # TODO what is current.source?  previous had: print(F"Syntax Error in line {current.line}: {bse.message}: {current.source}")
            except BasicRuntimeError as bre:
                self._run = RunStatus.END_ERROR_RUNTIME
                raise BasicRuntimeError(str(bre)) from bre
            except Exception as e:
                self._run = RunStatus.END_ERROR_INTERNAL
                raise BasicInternalError(F"Internal error in line {current.line}: {e}") from e

            if self._coverage is not None:
                self._coverage[current.line].add(self._location.offset)

            if self._goto: # If any control transfer has happened.
                if self._trace_file_like:
                    destination_line = self._program.get_line(self._goto.index).line
                    print(F"\tControl Transfer from line {self._location} TO line {destination_line}: {self._goto}.",
                          file=self._trace_file_like)

                self._location = self._goto
                self._goto = None
            else:
                # Advance to next statement, on this line or the next
                next_location = self.get_next_stmt()
                if next_location is None:
                    # End of program
                    self._run = RunStatus.END_OF_PROGRAM
                    self._location = ControlLocation(None, 0)
                else:
                    self._location = next_location

            if single_step:
                self._run = RunStatus.BREAK_STEP

    def get_current_line(self) -> ProgramLine:
        return self._program.get_line(self._location.index)

    def get_current_location(self)->ControlLocation:
        """
        Gets the index into self._program for the next line to be executed,
        and the offset into that line.

        Used externally by LIST.

        :return: The index
        """
        return self._location

    def get_current_index(self)->int:
        """
        Gets the index into self._program for the next line to be executed.
        Used externally by LIST.

        :return: The index
        """
        return self._location.index

    def get_program_lines(self, start: int = 0, count: Optional[int] = None) -> List[str]:
        """
        Returns a range of source lines. Used to implement the LIST command
        :return: list[str]
        """
        return self._program.get_lines_range(start, count)

    def get_program_lines2(self, start: int, end_index: int) -> List[str]:
        """
        Returns a range of source lines. Used to implement the LIST command
        :return: list[str]
        """
        return self._program.get_lines_range2(start, end_index)

    def get_current_stmt(self):  # Return type depends on statement types, keeping as is for now
        return self._program.get_line(self._location.index).stmts[self._location.offset]

    def at_end(self) -> bool:
        return self._location.index is None

    def do_for(self, var: str, stop: str, step: str, stmt: Optional[ControlLocation]) -> None:
        """
        Begin a FOR loop.

        The start index is set by the caller of this function.

        :param var: The index of the "FOR" loop
        :param stop: The upper limit expression as a string. In BASIC, it is inclusive.
        :param step: The step expression as a string. Both expressions can change during loop execution.
        :param stmt: The ControlLocation to return to for the next iteration
        :return:
        """
        # Note that var and start are evaluated before beginning, but stop and step
        # get re-evaluated at each loop
        assert_syntax(len(self._for_stack) < 1000, "FORs nested too deeply")

        # Some programs GOTO out of the middle of a FOR loop, and later come back into the start
        # of the "FOR" loop. This really isn't correct BASIC, I think, and results in the
        # "FOR" stack growing without bound.
        #
        # To deal with it, if the top record on the stack has
        # the same loop index, we will pop the old record and add the new one.
        # We are adding a new one, in case the loop parameters have changed.
        # It might be more correct to only allow one for loop per variable, so we'd
        # scan the stack and remove the previous one. But that gets complicated - do we
        # remove everything above the duplicated for loop? So, for now, we only touch the top entry
        new_for: ForRecord = ForRecord(var, stop, step, stmt)
        if self._for_stack:
            top = self._for_stack[-1]
            if top.var == new_for.var:
                self._for_stack.pop()

        self._for_stack.append(ForRecord(var, stop, step, stmt))

    def do_next_peek(self, var: str) -> ForRecord:
        """
        Checks to see if we are on the correct next, and get the for_record
        :param var:
        :return:
        """
        assert_syntax(len(self._for_stack) > 0, "NEXT without FOR")
        for_record = self._for_stack[-1]
        assert_syntax(for_record.var == var.upper(), F"Wrong NEXT. Expected {for_record.var}, got {var}")
        return for_record

    def do_next_pop(self, var: str) -> None:
        assert_syntax(len(self._for_stack) > 0, "NEXT without FOR")
        for_record = self._for_stack.pop()
        assert_syntax(for_record.var==var.upper(), F"Wrong NEXT. Expected {for_record.var}, got {var}")

    def get_symbol_count(self) -> int:
        """
        Get number of defined symbols. Used for testing. This deliberately does not count nested scopes.
        :return:
        """
        return self._symbols.local_length()

    def put_symbol(self, symbol: str, value: Any, symbol_type: SymbolType, arg: Optional[str]) -> None:
        """
        Adds a symbol to the current symbol table.

        Some versions of basic allow arrays to have the same names as scalar variables. You can tell the difference
        by context. Here we get an explicit type. On get_symbol(), the caller will have to tell us.

        :param symbol:
        :param value:
        :param symbol_type:
        :param arg:
        :return:
        """

        # TODO Maybe check is_valid_variable here? Have to allow user defined functions, and built-ins, though.
        if self._trace_file_like:
            print(F"\t\t{symbol}={value}, {symbol_type}", file=self._trace_file_like)
        if symbol in self._data_breakpoints:
            self._run = RunStatus.BREAK_DATA

        self._symbols.put_symbol(symbol.upper(), value, symbol_type, arg)

    def put_symbol_element(self, symbol: str, value: Any, subscripts: List[int]) -> None:
        # TODO Maybe check is_valid_variable here? Have to allow user defined functions, and built-ins, though.
        if self._trace_file_like:
            print(F"\t\t{symbol}{subscripts}={value}, array element", file=self._trace_file_like)
        target = self.get_symbol(symbol, SymbolType.ARRAY)
        target_type = self.get_symbol_type(symbol, SymbolType.ARRAY)
        assert_syntax(target_type==SymbolType.ARRAY, F"Can't subscript non-array {symbol} of type {target_type}")
        v = target
        for subscript in subscripts[:-1]:
            v = v[subscript]
        subscript = subscripts[-1]
        v[subscript] = value

    def find_line(self, line_number: int) -> ControlLocation:
        """
        Convert a program line number (like, "100") to the index into self._program.
        """
        return ControlLocation(self._program.find_line_index(line_number), 0)

    def goto_line(self, line: int) -> None:
        target = self.find_line(line)
        self._goto_location(target)

    def _goto_location(self, ct: ControlLocation) -> None:
        """
        This does an internal control transfer. It uses an index into the self._program list,
        rather than a BASIC line number.

        Note this does not change the location directly, it sets a flag so they will be changed later.
        :param ct:
        :return:
        """
        assert ControlLocation == type(ct)
        self._goto = ct

    def gosub(self, line_number: int) -> None:
        go_to = self.find_line(line_number)
        return_to = self.get_next_stmt()
        self._gosub_stack.append(return_to)
        self._goto_location(go_to)
        return

    def do_return(self) -> None:
        assert_syntax(len(self._gosub_stack), "RETURN without GOSUB")
        return_to = self._gosub_stack.pop()
        self._goto_location(return_to)
        return

    def get_next_stmt(self) -> Optional[ControlLocation]:
        """
        Get a pointer to the next statement that would normally be executed.
        This is the next statement, if there are more statements on this line,
        or the next line.
        This is used in for loops to set where the NEXT will return to
        GOSUB should also use this, but don't yet.
        :return: ControlLocation Object, pointing to the next statement.
        """
        return self._program.get_next_statement_location(self._location.index, self._location.offset)

    def _get_next_line(self) -> Optional[ControlLocation]:
        next_index = self._program.get_next_index(self._location.index)
        if next_index is None:
            # TODO Style: Should this return None, or ControlLocation(None,0), which is used above
            return None

        return ControlLocation(next_index, 0)

    def goto_next_line(self) -> None:
        """
        This is used by "IF ... THEN...", if the condition is false. It moves us to the next line, instead
        of continuing with the THEN clause.
        :return: None
        """
        location = self._get_next_line()
        if location is None:
            # If the condition was false, and if statement was the last line of program.
            self._run = RunStatus.END_OF_PROGRAM
            return

        self._goto_location(location)

    def goto_else(self) -> None:
        """
        When an if then condition is false, we scan the line for an else statement.
        transfers control to the statement after the else, or to the next line.
        # TODO: I don't think this will handle nested IFs. for that, I think we
        # have to scan for the Nth ELSE statement.
        """
        current_index = self._location.index
        current_offset = self._location.offset
        current_offset += 1
        current_line = self._program.get_line(current_index)
        while current_offset < len(current_line.stmts):
            if isinstance(current_line.stmts[current_offset], ParsedStatementElse):
                current_offset += 1
                # We want the statement AFTER the else, if any
                if current_offset < len(current_line.stmts):
                    location = ControlLocation(current_index, current_offset)
                    self._goto_location(location)
                    return
                else:
                    raise BasicSyntaxError("No clause with ELSE statement.")
                current_offset = 0
            current_offset += 1
        else:
            # No else found, go to the next line.
            self.goto_next_line()

    def is_symbol_defined(self, symbol: str, symbol_type: SymbolType = SymbolType.VARIABLE) -> bool:
        """
        :param symbol:
        :return: True if defined, else False
        """
        return self._symbols.is_symbol_defined(symbol, symbol_type)

    def get_symbol(self, symbol: str, symbol_type: SymbolType = SymbolType.VARIABLE) -> Any:
        # TODO Delete this. use get_symbol_value
        return self.get_symbol_value(symbol.upper(), symbol_type)

    def get_symbol_value(self, symbol: str, symbol_type: SymbolType = SymbolType.VARIABLE) -> Any:
        """
        :param symbol:
        :param symbol_type: Arrays, functions and Scalars all have their own namespaces
        :return:
        """
        return self._symbols.get_symbol_value(symbol.upper(), symbol_type)

    def get_symbol_type(self, symbol: str, symbol_type: SymbolType = SymbolType.VARIABLE) -> SymbolType:
        """
        :param symbol:
        :param symbol_type: Arrays, functions and Scalars all have their own namespaces
        :return:
        """
        return self._symbols.get_symbol_type(symbol, symbol_type)

    def do_print(self, msg: str, **kwargs) -> None:
        """
        This function exists so we can do redirection of output conveniently, for testing.
        :param msg:
        :return:
        """
        print(msg, **kwargs)

    def do_input(self) -> str:
        """
        This function exists so that we can do redirection of output conveniently, for testing.
        :return:
        """
        response = input()
        return response

    def read_data_value(self) -> Any:
        """
        Read the next DATA value from the program.
        Scans the program for DATA statements and returns the next value.
        """
        # Start from current position or beginning if not set
        if self._data_position is None:
            line_index = 0
            stmt_index = 0
            value_index = 0
        else:
            line_index, stmt_index, value_index = self._data_position

        # Scan through program starting from current position
        while line_index < len(self._program):
            program_line = self._program.get_line(line_index)
            
            # Start from stmt_index for current line, 0 for subsequent lines
            start_stmt = stmt_index if line_index == (self._data_position[0] if self._data_position else 0) else 0
            
            for s_index in range(start_stmt, len(program_line.stmts)):
                stmt = program_line.stmts[s_index]
                
                # Check if this is a DATA statement
                if stmt.keyword.name == 'DATA':
                    from basic_parsing import ParsedStatementData
                    # Start from value_index for current statement, 0 for subsequent statements  
                    start_value = value_index if (line_index == (self._data_position[0] if self._data_position else 0) and 
                                                 s_index == (self._data_position[1] if self._data_position else 0)) else 0
                    
                    if start_value < len(stmt._values):
                        # Found next data value
                        data_value = stmt._values[start_value]
                        # Update position to next value
                        next_value_index = start_value + 1
                        self._data_position = (line_index, s_index, next_value_index)
                        return data_value
            
            # Move to next line
            line_index += 1
            stmt_index = 0
            value_index = 0

        # No more data found
        raise BasicRuntimeError("I tried to READ, but ran out of data.")

    def restore_data(self, line_number: Optional[int] = None) -> None:
        """
        Reset the data pointer to the beginning of data or to a specific line.
        """
        if line_number is None:
            # Reset to beginning
            self._data_position = None
        else:
            # Find the specified line and verify it contains DATA
            found_data = False
            for line_index, program_line in enumerate(self._program):
                if program_line.line == line_number:
                    # Check if this line contains any DATA statements
                    for stmt_index, stmt in enumerate(program_line.stmts):
                        if stmt.keyword.name == 'DATA':
                            found_data = True
                            break
                    
                    if not found_data:
                        raise BasicRuntimeError(f"RESTORE {line_number}: Line does not contain DATA")
                    
                    # Set position to start of this line
                    self._data_position = (line_index, 0, 0)
                    return
            
            # Line not found
            raise BasicRuntimeError(f"RESTORE {line_number}: Line not found")
