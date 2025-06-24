"""
This module contains the class, Executor, that runs BASIC programs
"""
from collections import namedtuple, defaultdict
import random

import basic_functions
from basic_types import ProgramLine, BasicInternalError, assert_syntax, BasicSyntaxError
from basic_types import SymbolType, RunStatus
from basic_symbols import SymbolTable


# Target of a control transfer. Used by GOTO, GOSUB, NEXT, etc.
# TODO This should be a mutable class, and we should use it for the current instruction
# index: The index into the Executor._program list
# offset: The index into the Executor._program[x].stmts list.
class ControlLocation:
    def __init__(self, index, offset):
        self.index = index
        self.offset = offset


# var: the index variable
# stop: The ending value, and expression
# step: The step, and expression. both expressions can change during loop execution
# stmt: Used to tell if we are initializing the loop, or looping. Don't think this is used now.
# Note: we don't need to save "start" it's only used on setup.
ForRecord = namedtuple("ForRecord", "var stop step stmt")


class Executor:
    def restart(self):
        self._location = ControlLocation(0,0)
        self._goto = None
        self._gosub_stack = []
        self._for_stack = []


    def __init__(self, program:list[ProgramLine],
                 trace_file=None, stack_trace=False,
                 coverage=False,
                 record_inputs=False):
        """

        :param program:
        :param trace_file: Save a list of lines executed to a file for debugging
        :param record_inputs: TBD Record a list of lines entered by the user. Used for building test scripts.
        :param stack_trace: Rethrow BasicSyntaxErrors, so we get a stack trace.
        :param coverage: None, or a dict of (line_number:set of statements). Set to [] to enable coverage. Set to
        a coverage from a previous run, to add to that run
        """
        self._program = program
        self._location = ControlLocation(0,0)
        self._run = RunStatus.RUN
        self._trace_file = trace_file
        self._stack_trace = stack_trace
        self._goto = None
        self._gosub_stack = []
        self._for_stack = []
        # PyCharm complains if these are defined anywhere outside of __init__
        self._internal_symbols = None
        self._symbols = None
        self._data_breakpoints = []
        self._coverage = defaultdict(set) if coverage else None
        if self._coverage:
            print("Running with code coverage")
        self.init_symbols()
        self.setup_program()

    def init_symbols(self):
        self._internal_symbols = SymbolTable()
        self._symbols = self._internal_symbols.get_nested_scope()

    def set_trace_file(self, value):
        self._trace_file = value

    def setup_program(self):
        functions = basic_functions.PredefinedFunctions()
        for f in functions.functions:
            self._internal_symbols.put_symbol(f, "⌊", SymbolType.FUNCTION, arg=None)

        random.seed(1)

    def run_program(self, breaklist:list[tuple]=None, data_breakpoints:list[str]=None, single_step=False):
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
            breaklist: list[tuple] = []
        if data_breakpoints is None:
            data_breakpoints:list[str] = []
        self._run = RunStatus.RUN
        self._data_breakpoints = data_breakpoints

        while True:
            if self.at_end():
                self._run = RunStatus.END_OF_PROGRAM
                return self._run

            current = self.get_current_line()
            index = self.get_current_index()
            # If single step mode, allow them to go over the breakpoint they just hit.
            if not single_step:
                for breakpoint in breaklist:
                    if current.line == breakpoint[0]:
                        if self._location.offset == breakpoint[1]:
                            self._run = RunStatus.BREAK_CODE

            if self._run != RunStatus.RUN:
                return self._run

            if self._trace_file and self._location.offset==0:
                print(F">{current.source}", file=self._trace_file)

            s = self.get_current_stmt()

            if self._trace_file:
                # TODO ParsedStatements should have a __str__. Not everything is in args anymore.`
                print(F"\t{s.keyword.name} {s.args}", file=self._trace_file)

            execution_function = s.keyword.value.get_exec()
            try:
                execution_function(self, s)
            except BasicSyntaxError as bse:
                # TODO: This needs a bit more thought. The tests are checking for exceptions,
                # TODO and don't need the print statement. The user just needs the message printed.
                self._run = RunStatus.END_ERROR_SYNTAX
                raise BasicSyntaxError(bse.message, current.line)
                # TODO what is current.source?  previous had: print(F"Syntax Error in line {current.line}: {bse.message}: {current.source}")
            except Exception as e:
                self._run = RunStatus.END_ERROR_INTERNAL
                raise BasicInternalError(F"Internal error in line {current.line}: {e}")

            if self._coverage is not None:
                self._coverage[current.line].add(self._location.offset)

            # Advance to next statement, on this line or the next
            self._location = self.get_next_stmt()

            if self._goto: # If any control transfer has happened.
                if self._trace_file:
                    destination_line = self._program[self._goto.index].line
                    print(F"\tControl Transfer from line {self._location} TO line {destination_line}: {self._goto}.",
                          file=self._trace_file)

                self._location = self._goto
                self._goto = None
            if single_step:
                self._run = RunStatus.BREAK_STEP

    def get_current_line(self):
        return self._program[self._location.index]

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

    def get_program_lines(self, start=0, count=None)->list[str]:
        """
        Returns a range of source lines. Used to implement the LIST command
        :return: list[str]
        """
        length = len(self._program)
        if count is None:
            count = length

        assert_syntax(0 <= start < length, "Line number out of range.")
        stop = start + count
        if stop >= length:
            stop = length
        lines = [line.source for line in self._program[start:stop]]
        return lines

    def get_current_stmt(self):
        return self._program[self._location.index].stmts[self._location.offset]

    def at_end(self):
        return self._location.index is None

    def do_for(self, var, stop, step, stmt):
        """
        Begin a FOR loop.

        The start index is set by the caller of this function.

        :param var: The index of the "FOR" loop
        :param stop: The upper limit. In BASIC, it is inclusive.
        :param step: The amount to increment the index after each loop.
        :param stmt:
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
        new_for = ForRecord(var, stop, step, stmt)
        if self._for_stack:
            top = self._for_stack[-1]
            if top.var == new_for.var:
                self._for_stack.pop()

        self._for_stack.append(ForRecord(var, stop, step, stmt))

    def do_next_peek(self, var):
        """
        Checks to see if we are on the correct next, and get the for_record
        :param var:
        :return:
        """
        assert_syntax(len(self._for_stack) > 0, "NEXT without FOR")
        for_record = self._for_stack[-1]
        assert_syntax(for_record.var==var, F"Wrong NEXT. Expected {for_record.var}, got {var}")
        return for_record

    def do_next_pop(self, var):
        assert_syntax(len(self._for_stack) > 0, "NEXT without FOR")
        for_record = self._for_stack.pop()
        assert_syntax(for_record.var==var, F"Wrong NEXT. Expected {for_record.var}, got {var}")

    def get_symbol_count(self):
        """
        Get number of defined symbols. Used for testing. This deliberately does not count nested scopes.
        :return:
        """
        return self._symbols.local_length()

    def put_symbol(self, symbol:str, value, symbol_type:SymbolType, arg:str)->None:
        """
        Adds a symbol to a the current symbol table.

        Some versions of basic allow arrays to have the same names as scalar variables. You can tell the difference
        by context. Here we get an explicit type. On get_symbol(), the caller will have to tell us.

        :param symbol:
        :param value:
        :param symbol_type:
        :param arg:
        :return:
        """

        # TODO Maybe check is_valid_variable here? Have to allow user defined functions, and built-ins, though.
        if self._trace_file:
            print(F"\t\t{symbol}={value}, {symbol_type}", file=self._trace_file)
        if symbol in self._data_breakpoints:
            self._run = RunStatus.BREAK_DATA

        self._symbols.put_symbol(symbol, value, symbol_type, arg)

    def put_symbol_element(self, symbol, value, subscripts):
        # TODO Maybe check is_valid_variable here? Have to allow user defined functions, and built-ins, though.
        if self._trace_file:
            print(F"\t\t{symbol}{subscripts}={value}, array element", file=self._trace_file)
        target = self.get_symbol(symbol, SymbolType.ARRAY)
        target_type = self.get_symbol_type(symbol, SymbolType.ARRAY)
        assert_syntax(target_type==SymbolType.ARRAY, F"Can't subscript non-array {symbol} of type {target_type}")
        v = target
        for subscript in subscripts[:-1]:
            v = v[subscript]
        subscript = subscripts[-1]
        v[subscript] = value

    def find_line(self, line_number):
        for index, possible in enumerate(self._program):
            if possible.line == line_number:
                return ControlLocation(index=index, offset=0)
        raise BasicSyntaxError(F"No line {line_number} found.")

    def goto_line(self, line):
        target = self.find_line(line)
        self._goto_location(target)

    def _goto_location(self, ct):
        """
        This does an internal control transfer. It uses an index into the self._program list,
        rather than a BASIC line number.

        Note this does not change the location directly, it sets a flag so they will be changed later.
        :param ct:
        :return:
        """
        assert ControlLocation == type(ct)
        self._goto = ct

    def gosub(self, line_number):
        go_to = self.find_line(line_number)
        return_to = self.get_next_stmt()
        self._gosub_stack.append(return_to)
        self._goto_location(go_to)
        return

    def do_return(self):
        assert_syntax(len(self._gosub_stack), "RETURN without GOSUB")
        return_to = self._gosub_stack.pop()
        self._goto_location(return_to)
        return

    def get_next_stmt(self):
        """
        Get a pointer to the next statement that would normally be executed.
        This is the next statement, if there are more statements on this line,
        or the next line.
        This is used it for loops to set where the NEXT will return to
        GOSUB should also use this, but don't yet.
        :return: ControlLocation Object, pointing to the next statement.
        """
        # 'line' refers to an index into the self._program list, not a basic line number.
        current_index = self._location.index
        current_offset = self._location.offset
        current_offset += 1
        if current_offset >= len(self._program[current_index].stmts):
            current_index = self._program[current_index].next
            current_offset = 0
        return ControlLocation(current_index, current_offset)

    def _get_next_line(self):
        next_index = self._program[self._location.index].next
        if next_index is None:
            # TODO Style: Should this return None, or ControlLocation(None,0), which is used above
            return None

        return ControlLocation(next_index, 0)

    def goto_next_line(self):
        """
        This is used by "IF ... THEN...", if the condition is false. It moves us to the next line, instead
        of continuing with the THEN clause.
        :return: None
        """
        location = self._get_next_line()
        if location is None:
            # If condition was false, and if statement was last line of program.
            self._run = RunStatus.END_OF_PROGRAM
            return

        self._goto_location(location) # why do we need to hunt for the line? We know the index, and can go directly.

    def is_symbol_defined(self, symbol, symbol_type:SymbolType=SymbolType.VARIABLE):
        """
        :param symbol:
        :return: True if defined, else False
        """
        return self._symbols.is_symbol_defined(symbol, symbol_type)

    def get_symbol(self, symbol, symbol_type:SymbolType=SymbolType.VARIABLE):
        # TODO Delete this. use get_symbol_value
        return self.get_symbol_value(symbol, symbol_type)

    def get_symbol_value(self, symbol, symbol_type:SymbolType=SymbolType.VARIABLE):
        """
        :param symbol:
        :param symbol_type: Arrays, functions and Scalars all have their own namespaces
        :return:
        """
        return self._symbols.get_symbol_value(symbol, symbol_type)

    def get_symbol_type(self, symbol, symbol_type:SymbolType=SymbolType.VARIABLE):
        """
        :param symbol:
        :param symbol_type: Arrays, functions and Scalars all have their own namespaces
        :return:
        """
        return self._symbols.get_symbol_type(symbol, symbol_type)

    def do_print(self, msg, **kwargs):
        """
        This function exists so we can do redirection of output conveniently, for testing.
        :param msg:
        :return:
        """
        print(msg, **kwargs)

    def do_input(self):
        """
        This function exists so that we can do redirection of output conveniently, for testing.
        :return:
        """
        response = input()
        return response

    # Is this needed?
    # def _get_current_line_number(self):
    #     """
    #     Gets the line_number that is next to be executed.
    #     :return:
    #     """
    #     current = self._program[self._location.index]
    #     line_number = current.line
    #     return line_number