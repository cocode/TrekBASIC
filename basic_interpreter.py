"""
This module contains the code the execute BASIC commands, and the class
that runs the program (Executor)
"""
import traceback
from collections import namedtuple
from enum import Enum, auto
import random

from basic_types import ProgramLine, BasicSyntaxError, BasicInternalError, assert_syntax
from basic_types import SymbolType, RunStatus
from basic_symbols import SymbolTable
from basic_utils import smart_split
from basic_statements import Keywords


# def is_string_variable(variable:str):
#     return variable.endswith("$")
#
#
# def is_valid_identifier(variable:str):
#     """
#     Checks if the identifier is a valid variable name to assign to.
#     Assumes that spaces have already been removed.
#     Does not recognize internal functions, or user defined functions.
#     :param variable: The variable name to check.
#     :return: None. Raises an exception if the name is not valid.
#     """
#     assert_syntax(len(variable) >= 1, F"Zero length variable name.")
#     assert_syntax(len(variable) <= 3, F"Variable {variable} too long.")
#     assert_syntax(variable[0] in LETTERS, F"Variable {variable} must start with a letters.")
#     if len(variable) == 1:
#         return
#     if len(variable) == 2 and variable[1] == '$':
#         return
#     assert_syntax(variable[1] in NUMBERS, "Second char of {variable} must be a number or $.")
#     if len(variable) == 2:
#         return
#     assert_syntax(variable[2] == '$', F"Invalid variable name {variable}")
#
#
# def assign_variable(executor, variable, value):
#     """
#     Variable assignment can include assigning array elements.
#     :param variable:
#     :param value:
#     :return:
#     """
#     variable = variable.replace(" ", "")
#     # Need to handle two dimensional array element assignment.
#     i = variable.find("(")
#     if i != -1:
#         # Array reference
#         j = variable.find(")", i+1)
#         if j == -1:
#             raise BasicSyntaxError(F"Missing ) in in array assignment to {variable}")
#         if i+1 == j:
#             raise BasicSyntaxError(F"Missing array subscript in assignment to {variable}")
#
#         subscripts = variable[i+1:j].split(",")
#         variable = variable[:i]
#         is_valid_identifier(variable)
#         subscripts = [int(eval_expression(executor._symbols, subscript)) - 1 for subscript in subscripts]
#         executor.put_symbol_element(variable, value, subscripts)
#     else:
#         is_valid_identifier(variable)
#         executor.put_symbol(variable, value, symbol_type=SymbolType.VARIABLE, arg=None)
#
#
# def eval_expression(symbols, value):
#     lexer = Lexer()
#     tokens = lexer.lex(value)
#     e = Expression()
#     result = e.eval(tokens, symbols=symbols)
#     return result
#

def tokenize_statements(commands_text:list[str]):
    """
    Parses individual statements. A ine of the program may have multiple statements in it.

    This line has three statements.

    100 A=3:PRINT"A is equal to";A:X=6

    :param commands_text:
    :return:
    """
    list_of_statements = []
    options = [cmd for cmd in Keywords.__members__.values()]
    for command in commands_text:
        command = command.lstrip()
        for cmd in options:         # Can't just use a dict, because of lines like "100 FORX=1TO10"
            if command.startswith(cmd.name):
                parser_for_keyword = cmd.value.get_parser_class()
                parsed_statement = parser_for_keyword(cmd, command[len(cmd.name):])
                break
        else:
            # Assignment expression is the default
            cmd = Keywords.LET
            parser_for_keyword = cmd.value.get_parser_class()
            parsed_statement = parser_for_keyword(cmd, command)

        list_of_statements.append(parsed_statement)
        # This picks up the clauses after then "THEN" in an "IF ... THEN ..."
        additional_text = parsed_statement.get_additional()
        commands_array = smart_split(additional_text)
        for i in range(len(commands_array)):
            # Handle special case of "IF x THEN X=3:100"
            if commands_array[i].strip().isdigit():
                commands_array[i] = "GOTO "+commands_array[i]
        additional = tokenize_statements(commands_array)
        list_of_statements.extend(additional)

    return list_of_statements


def tokenize_line(program_line: str) -> ProgramLine:
    """
    Converts the line into a partially digested form. tokenizing basic is mildly annoying,
    as there may not be a delimiter between the cmd and the args. Example:

    FORI=1TO8:FORJ=1TO8:K3=0:Z(I,J)=0:R1=RND(1)

    The FOR runs right into the I.

    So we need to prefix search.
    :param program_line:
    :return:
    """
    if len(program_line) == 0:
        return None
    number, partial = program_line.split(" ", 1)
    assert_syntax(str.isdigit(number), F"Line number is not in correct format: {number}")
    number = int(number)

    # Rem commands don't split on colons, other lines do.
    if partial.startswith(Keywords.REM.name):
        commands_text = [partial]
    else:
        commands_text = smart_split(partial)
    try:
        list_of_statements = tokenize_statements(commands_text)
    except BasicSyntaxError as bse:
        print(F"Syntax Error in line {number}: {bse.message}: {program_line}")
        print()
        raise bse
    s = ProgramLine(number, list_of_statements, -1, source=program_line)
    return s


def tokenize(program_lines:list[str]) -> list[ProgramLine]:
    tokenized_lines = []
    last_line = None
    for line in program_lines:
        tokenized_line = tokenize_line(line)
        if tokenized_line is None:
            continue    # Ignore blank lines.
        if last_line is not None:
            assert_syntax(tokenized_line.line > last_line, F"Line {tokenized_line.line} is <= the preceding line {line}")
        tokenized_lines.append(tokenized_line)
        last_line = tokenized_line.line

    # Set default execution of next line.
    finished_lines = []
    if len(tokenized_lines): # Deal with zero length files.
        for i in range(len(tokenized_lines)-1):
            finished_lines.append(ProgramLine(tokenized_lines[i].line,
                                             tokenized_lines[i].stmts,
                                             i+1,
                                             source=tokenized_lines[i].source))
        finished_lines.append(ProgramLine(tokenized_lines[-1].line,
                                         tokenized_lines[-1].stmts,
                                         None,
                                         source=tokenized_lines[-1].source))
    return finished_lines


def load_program(program_filename):
    with open(program_filename) as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    program = tokenize(lines)
    return program


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
    def __init__(self, program:list[ProgramLine], trace_file=None, stack_trace=False):
        """

        :param program:
        :param trace_file: Save a list of lines executed to a file for debugging
        :param stack_trace: Rethrow BasicSyntaxErrors, so we get a stack trace.
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
        self.init_symbols()
        self.setup_program()

    def init_symbols(self):
        self._internal_symbols = SymbolTable()
        self._symbols = self._internal_symbols.get_nested_scope()

    def set_trace_file(self, value):
        self._trace_file = value

    def setup_program(self):
        self._internal_symbols.put_symbol("INT", "⌊", SymbolType.FUNCTION, arg=None) # TODO Should actual lambda be here?
        self._internal_symbols.put_symbol("RND", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("SGN", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("LEFT$", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("RIGHT$", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("MID$", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("LEN", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("TAB", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("STR$", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("SPACE$", "⌊", SymbolType.FUNCTION, arg=None)
        random.seed(1)

    def run_program(self, breaklist:list[str]=[], data_breakpoints:list[str]=[]):
        """
        Run the program. This can also be called to resume after a breakpoint.

        Data breakpoints happen AFTER the statement containing the access has completed.
        It would require substantial overhead to break BEFORE the statement, but it was
        almost free to break after.
        Since data breakpoints happen after the statement has completed, we also have to
        allow control transfers for the statement to happen, like going to the next line,
        otherwise the line would execute again when continuing.

        :param breaklist: A list of str - program line numbers to break before.
        :param A value from RunStatus
        """
        self._run = RunStatus.RUN
        self._data_breakpoints = data_breakpoints

        while True:
            if self.at_end():
                self._run = RunStatus.END_OF_PROGRAM
                return self._run

            current = self.get_current_line()
            if current.line in breaklist:
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
                print(F"Syntax Error in line {current.line}: {bse.message}: {current.source}")
                if self._stack_trace:
                    raise bse
            except Exception as e:
                traceback.print_exc()
                self._run = RunStatus.END_ERROR_INTERNAL
                raise BasicInternalError(F"Internal error in line {current.line}: {e}")

            # Advance to next statement, on this line or the next
            self._location = self.get_next_stmt()

            if self._goto: # If any control transfer has happened.
                if self._trace_file:
                    destination_line = self._program[self._goto.index].line
                    print(F"\tControl Transfer from line {self._location} TO line {destination_line}: {self._goto}.",
                          file=self._trace_file)

                self._location = self._goto
                self._goto = None

    def get_current_line(self):
        return self._program[self._location.index]

    def get_current_index(self)->int:
        """
        Gets the index into self._program for the next line to be executed.
        Used externally by LIST.

        :return: The index
        """
        return self._location.index

    def get_program_lines(self, start, count)->list[str]:
        """
        Returns a range of source lines. Used to implement the LIST command
        :return: list[str]
        """
        length = len(self._program)
        assert_syntax(0 <= start < length, "Line number out of range.")
        stop = start + count
        if stop >= length:
            stop = length - 1
        lines = [line.source for line in self._program[start:]]
        return lines

    def get_current_stmt(self):
        return self._program[self._location.index].stmts[self._location.offset]

    def at_end(self):
        return self._location.index is None

    def do_for(self, var, start, stop, step, stmt):
        """
        Begin a FOR loop.

        :param var: The index of the FOR loop
        :param start: The starting value
        :param stop: The upper limit. In BASIC, it is inclusive.
        :param step: The amount to increment the index after each loop.
        :param stmt:
        :return:
        """
        # Note that var and start are evaluated before beginning, but stop and step
        # get re-evaluated at each loop
        assert_syntax(len(self._for_stack) < 1000, "FORs nested too deeply")
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
        return len(self._symbols)

    def put_symbol(self, symbol, value, symbol_type, arg):
        # TODO Maybe check is_valid_variable here? Have to allow user defined functions, and built-ins, though.
        if self._trace_file:
            print(F"\t\t{symbol}={value}, {symbol_type}", file=self._trace_file)
        if self._data_breakpoints and symbol in self._data_breakpoints:
            self._run = RunStatus.BREAK_DATA
        self._symbols.put_symbol(symbol, value, symbol_type, arg)

    def put_symbol_element(self, symbol, value, subscripts):
        # TODO Maybe check is_valid_variable here? Have to allow user defined functions, and built-ins, though.
        if self._trace_file:
            print(F"\t\t{symbol}{subscripts}={value}, array element", file=self._trace_file)
        target = self.get_symbol(symbol)
        target_type = self.get_symbol_type(symbol)
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
        :param line:
        :return:
        """
        location = self._get_next_line()
        if location is None:
            # If condition was false, and if statement was last line of program.
            self._run = RunStatus.END_OF_PROGRAM
            return

        self._goto_location(location) # why do we need to hunt for the line? We know the index, and can go directly.

    def is_symbol_defined(self, symbol):
        """
        :param symbol:
        :return: True if defined, else False
        """
        return self._symbols.is_symbol_defined(symbol)

    def get_symbol(self, symbol): # TODO Delete this. use get_symbol_value
        return self.get_symbol_value(symbol)

    def get_symbol_value(self, symbol):
        """
        :param symbol:
        :return:
        """
        return self._symbols.get_symbol(symbol)

    def get_symbol_type(self, symbol):
        """
        :param symbol:
        :return:
        """
        return self._symbols.get_symbol_type(symbol)

    def _get_current_line_number(self):
        """
        Gets the line_number that is next to be executed.
        :return:
        """
        current = self._program[self._location.index]
        line_number = current.line
        return line_number