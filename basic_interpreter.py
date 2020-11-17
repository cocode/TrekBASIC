"""
Basic interpreter to run superstartrek.
It's not intended (yet) to run ANY basic program.
"""
import traceback
from collections import namedtuple
import sys
from enum import Enum
import random

from basic_types import ProgramLine, lexer_token, BasicSyntaxError, BasicInternalError, assert_syntax, ste, SymbolType
from parsed_statements import ParsedStatement, ParsedStatementIf, ParsedStatementFor, ParsedStatementOnGoto
from parsed_statements import ParsedStatementInput
from basic_lexer import lexer_token, Lexer, NUMBERS, LETTERS
from basic_expressions import Expression
from basic_symbols import SymbolTable
from basic_utils import smart_split




# For now, don't tokenize in advance
def stmt_rem(executor, stmt):
    """
    Does nothing.
    :return:
    """
    return None

# TODO can print be more complex? PRINT A$,"ABC",B$. I think it can
def stmt_print(executor, stmt):
    arg = stmt.args.strip()
    args = arg.split(";")
    for i, arg in enumerate(args):
        arg = arg.strip()
        if len(arg) == 0:
            continue
        if arg[0] == '"': # quoted string
            assert_syntax(arg[0] =='"' and arg[-1] == '"', "String not properly quoted for 'PRINT'")
            output = arg[1:-1]
            print(output, end='')
        else: # Expression
            v = eval_expression(executor._symbols, arg)
            #v = executor.get_symbol(arg)
            if type(v) == float:
                print(F" {v:g} ", end='') # I'm trying to figure out the rules for spacing.
                                          # NO spaces is wrong (see initial print out)
                                          # Spaces around everything is wrong.
                                          # Spaces around numbers but not strings seems to work, so far.
            else:
                print(F"{v}", end='')

        # if i < len(args) - 1:
        #     print(" ", end='')
    print()
    return None


def stmt_goto(executor, stmt):
    destination = stmt.args.strip()
    assert_syntax(str.isdigit(destination), F"Goto target is not an int ")
    executor.goto_line(int(destination))
    return None


def stmt_gosub(executor, stmt):
    destination = stmt.args.strip()
    assert_syntax(str.isdigit(destination), F"Gosub target is not an int ")
    executor.gosub(int(destination))
    return None


def stmt_for(executor, stmt:ParsedStatementFor):
    var = stmt._index_clause
    start = stmt._start_clause
    start = eval_expression(executor, start)
    is_valid_identifier(var)
    executor.put_symbol(var, start, SymbolType.VARIABLE, None)
    executor.do_for(var, start, stmt._to_clause, stmt._step_clause, executor.get_next_stmt())


def stmt_next(executor, stmt):
    index = stmt.args.strip()
    var, to_clause, step_clause, loop_top = executor.do_next_peek(index)
    value = executor.get_symbol(var)
    to_value = eval_expression(executor._symbols, to_clause)
    step_value = eval_expression(executor._symbols, step_clause)
    value = value + step_value
    executor.put_symbol(var, value, SymbolType.VARIABLE, None)
    if value <= to_value:
        executor._goto_location(loop_top)
    else:
        executor.do_next_pop(var)

def is_string_variable(variable:str):
    return variable.endswith("$")

def is_valid_identifier(variable:str):
    """
    Checks if the identifier is a valid variable name to assign to.
    Assumes that spaces have already been removed.
    Does not recognize internal functions, or user defined functions.
    :param variable: The variable name to check.
    :return: None. Raises an exception if the name is not valid.
    """
    assert_syntax(len(variable) >= 1, F"Zero length variable name.")
    assert_syntax(len(variable) <= 3, F"Variable {variable} too long.")
    assert_syntax(variable[0] in LETTERS, F"Variable {variable} must start with a letters.")
    if len(variable) == 1:
        return
    if len(variable) == 2 and variable[1] == '$':
        return
    assert_syntax(variable[1] in NUMBERS, "Second char of {variable} must be a number or $.")
    if len(variable) == 2:
        return
    assert_syntax(variable[2] == '$', F"Invalid variable name {variable}")


def assign_variable(executor, variable, value):
    """
    Variable assignment can include assigning array elements.
    :param variable:
    :param value:
    :return:
    """
    variable = variable.replace(" ", "")
    # Need to handle two dimensional array element assignment.
    i = variable.find("(")
    if i != -1:
        # Array reference
        j = variable.find(")", i+1)
        if j == -1:
            raise BasicSyntaxError(F"Missing ) in in array assignment to {variable}")
        if i+1 == j:
            raise BasicSyntaxError(F"Missing array subscript in assignment to {variable}")

        subscripts = variable[i+1:j].split(",")
        variable = variable[:i]
        is_valid_identifier(variable)
        subscripts = [int(eval_expression(executor._symbols, subscript)) - 1 for subscript in subscripts]
        executor.put_symbol_element(variable, value, subscripts)
    else:
        is_valid_identifier(variable)
        executor.put_symbol(variable, value, symbol_type=SymbolType.VARIABLE, arg=None)


def eval_expression(symbols, value):
    lexer = Lexer()
    tokens = lexer.lex(value)
    e = Expression()
    result = e.eval(tokens, symbols=symbols)
    return result

def stmt_let(executor, stmt):
    try:
        variable, value = stmt.args.split("=", 1)
    except Exception as e:
        raise BasicSyntaxError(F"Error in expression. No '='.")

    variable = variable.strip()
    result = eval_expression(executor._symbols, value)
    assign_variable(executor, variable, result)


def stmt_clear(executor, stmt):
    # Clear statement removes all variables.
    executor.init_symbols()

def stmt_dim(executor, stmt):
    # TODO Handle variables in array dimensions?
    stmts = smart_split(stmt.args.strip(), "(", ")", ",")
    for s in stmts:
        s = s.strip()
        # TODO a 'get_identifier' function
        name = s[0]
        assert_syntax(len(s) > 1, "Missing dimensions")
        if s[1] in NUMBERS:
            name += s[1]
        if s[len(name)] == "$":
            name += "$"
        dimensions = s[len(name):]
        assert_syntax(dimensions[0] == '(',  "Missing (")
        assert_syntax(dimensions[-1] == ')', "Missing (")
        dimensions = dimensions[1:-1] # Remove parens
        dimensions = dimensions.split(",")
        assert len(dimensions) <= 2 and len(dimensions) > 0
        if len(dimensions) == 1:
            size = int(dimensions[0])
            value = [0] * size
        if len(dimensions) == 2:
            size_x = int(dimensions[0].replace("(",''))
            size_y = int(dimensions[1].replace(")",''))
            value = [ [0] * size_y for _ in range(size_x)] # wrong: [[0] * size_y] * size_x
        executor.put_symbol(name, value, SymbolType.ARRAY, arg=None) # Not right, but for now.


def stmt_if(executor, stmt):
    """
    An if statement works by skipping to the next line, if the THEN clause is false, otherwise
    it continues to execute the clauses after the THEN.
    :param executor:
    :param stmt:
    :return:
    """
    lexer = Lexer()
    tokens = lexer.lex(stmt.args)
    e = Expression()
    result = e.eval(tokens, symbols=executor._symbols)
    if not result:
        executor.goto_next_line()


def stmt_input(executor, stmt):
    var = stmt._input_var
    is_valid_identifier(var)
    prompt = stmt._prompt
    # Not sure if this can be an expression. None are used in my examples, but why not?
    if prompt:
        prompt = eval_expression(executor._symbols, prompt)
    print(prompt, end='')
    result = input()
    if not is_string_variable(var):
        result = float(result)
    executor.put_symbol(var, result, SymbolType.VARIABLE, None)

def stmt_on(executor, stmt):
    var = stmt._expression
    op = stmt._op
    result = eval_expression(executor._symbols, var)
    assert_syntax(type(result) == int or type(result) == float, "Expression not numeric in ON GOTO/GOSUB")
    result = int(result) - 1 # Basic is 1-based.
    assert_syntax(result < len(stmt._target_lines), "No target for value of {result} in ON GOTO/GOSUB")
    if op == "GOTO":
        executor.goto_line(stmt._target_lines[result])
    elif op == "GOSUB":
        executor.gosub(stmt._target_lines[result])
    else:
        assert_syntax(False, "Bad format for ON statement.")


def stmt_end(executor, stmt):
    print("Ending program")
    executor._run = False
    executor.halt()


def stmt_def(executor, stmt):
    """
    Define a user-defined function.

    470 DEF FND(D)=SQR((K(I,1)-S1)^2+(K(I,2)-S2)^2)

    :param executor:
    :param stmt:
    :return:
    """
    try:
        variable, value = stmt.args.split("=", 1)
    except Exception as e:
        print(e)
    variable = variable.strip()
    assert_syntax(len(variable) == 6 and
                  variable.startswith("FN") and
                  variable[3]=='(' and
                  variable[5]==')',
                  "Function definition error")
    arg = variable[4]
    variable = variable[:3]
    value = value.strip()
    executor.put_symbol(variable, value, SymbolType.FUNCTION, arg)

def stmt_return(executor, stmt):
    executor.do_return()


class KB:
    def __init__(self, exec, parser_class=ParsedStatement):
        self._parser = parser_class
        self._exec = exec

    def get_parser_class(self):
        return self._parser

    def get_exec(self):
        return self._exec


class Keywords(Enum):
    CLEAR = KB(stmt_clear)
    DEF = KB(stmt_def) # User defined functions
    DIM = KB(stmt_dim)
    END = KB(stmt_end)
    FOR = KB(stmt_for, ParsedStatementFor)
    GOTO = KB(stmt_goto)
    GOSUB = KB(stmt_gosub)
    IF = KB(stmt_if, ParsedStatementIf)
    INPUT = KB(stmt_input, ParsedStatementInput)
    LET = KB(stmt_let)
    NEXT = KB(stmt_next)
    ON = KB(stmt_on, ParsedStatementOnGoto) # Computed gotos, gosubs
    PRINT = KB(stmt_print)
    REM = KB(stmt_rem)
    RETURN = KB(stmt_return)


def tokenize_statements(commands_text:str):
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
            if commands_array[i].isdigit():
                commands_array[i] = "GOTO "+commands_array[i]
        additional = tokenize_statements(commands_array)
        list_of_statements.extend(additional)

    return list_of_statements

def tokenize_line(program_line: object) -> ProgramLine:
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


# Target of a control transfer
# index: The index into the Executor._program list
# offset: The index into the Exector._program[x].stmts list.
ControlLocation = namedtuple("ControlLocation", "index offset")
# var: the index variable
# stop: The ending value, and expression
# step: The step, and expression. both expressions can change during loop execution
# stmt: Used to tell if we are initializing the loop, or looping
# Note: we don't need to save "start" it's only used on setup.
ForRecord = namedtuple("ForRecord", "var stop step stmt")

class Executor:
    def __init__(self, program:list[ProgramLine], trace_file=None, stack_trace=False):
        """

        :param program:
        :param trace: Print basic line numbers during execution
        :param stack_trace: Rethrow BasicSyntaxErrors, so we get a stack trace.
        """
        self._program = program
        self._index = 0
        self._run = False
        self._trace_file = trace_file
        self._stack_trace = stack_trace
        self._goto = None
        # _statement_offset is used when we transfer control into the middle of a line
        # 100 PRINT"BEFORE":GOSUB 110:PRINT"AFTER"
        # When we RETURN, we should continue with PRINT"AFTER"
        self._statement_offset = 0
        self._gosub_stack = []
        self._stmt_index = 0
        self._for_stack = []
        # PyCharm complains if these are defined anywhere outside of __init__
        self._internal_symbols = None
        self._symbols = None
        self.init_symbols()
        self.setup_program()


    def init_symbols(self):
        self._internal_symbols = SymbolTable()
        self._symbols = self._internal_symbols.get_nested_scope()


    def set_trace_file(self, value):
        self._trace_file = value

    def halt(self):
        self._run = False

    def setup_program(self):
        # Vocabulary I will use going forward:
        # LINE refers to a basic line number
        # INDEX refers to the index into the list of LINES (self._program)
        # OFFSET refers to the index into the current LINE's list of statements.
        self._internal_symbols.put_symbol("INT", "⌊", SymbolType.FUNCTION, arg=None) # TODO Should actual lamdba be here?
        self._internal_symbols.put_symbol("RND", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("SGN", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("LEFT$", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("RIGHT$", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("MID$", "⌊", SymbolType.FUNCTION, arg=None)
        self._internal_symbols.put_symbol("LEN", "⌊", SymbolType.FUNCTION, arg=None)

        self._run = True
        self._count_lines = 0
        self._count_stmts = 0
        self._statement_offset = 0
        random.seed(1)

    def run_program(self, breaklist = []):
        while self._run:
            self.execute_current_line()
            current = self._program[self._index]
            line = current.line
            if line in breaklist:
                return 1
        return 0

    def execute_current_line(self):
            current = self._program[self._index]
            self._count_lines += 1
            if self._trace_file:
                print(F">{current.source}", file=self._trace_file)
            # Get the statements on the current line
            stmts = current.stmts
            for self._stmt_index in range(self._statement_offset, len(stmts)):
                s = stmts[self._stmt_index]
                self._count_stmts += 1
                if self._trace_file:
                    # TODO ParsedStatements should have a __str__. Not everything is in args anymore.`
                    print(F"\t{s.keyword.name} {s.args}", file=self._trace_file)
                execution_function = s.keyword.value.get_exec()
                try:
                    execution_function(self, s)
                except BasicSyntaxError as bse:
                    # TODO: This needs a bit more thought. The tests are checking for exceptions,
                    # TODO and don't need the print statement. The user just needs the message printed.
                    print(F"Syntax Error in line {current.line}: {bse.message}: {current.source}")

                    if self._stack_trace:
                        raise bse
                    self._run = False
                except Exception as e:
                    traceback.print_exc()
                    raise BasicInternalError(F"Internal error in line {current.line}: {e}")
                if not self._run:
                    break # Don't do the rest of the line
                if self._goto: # If a goto has happened.
                    if self._trace_file:
                        destination_line = self._program[self._goto.index].line
                        print(F"\tControl Transfer from line {current.line}:{self._stmt_index} TO line {destination_line}: {self._goto}.",
                              file=self._trace_file)

                    self._index = self._goto.index
                    self._statement_offset = self._goto.offset
                    self._goto = None
                    # Note: Have to check for a goto within a line! 100 print:print:goto 100:print "shouldn't see this"
                    break # This will skip the "else" which does the normal "step to next line"
            else:
                if current.next is None:
                    self._run = False
                else:
                    self._index = current.next
                self._statement_offset = 0

    def get_current_line(self):
        return self._program[self._index]

    def do_for(self, var, start, stop, step, stmt):
        # Note that var and start are evaluated before beginning, but stop and step
        # get re-evaluated at each loop
        assert_syntax(len(self._for_stack) < 1000, "FORs nested too deeply")
        self._for_stack.append(ForRecord(var, stop, step, stmt))

    def do_next_peek(self, var):
        """
        Checks to see if we are on the correct next, and get
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
        self._symbols.put_symbol(symbol, value, symbol_type, arg)

    def put_symbol_element(self, symbol, value, subscripts):
        # TODO Maybe check is_valid_variable here? Have to allow user defined functions, and built-ins, though.
        if self._trace_file:
            print(F"\t\t{symbol}{subscripts}={value}, array element", file=self._trace_file)
        target = self.get_symbol(symbol)
        target_type = self.get_symbol_type(symbol)
        assert_syntax(target_type==SymbolType.ARRAY, "Can't subscript a non-array")
        v = target
        for subscript in subscripts[:-1]:
            v = v[subscript]
        subscript = subscripts[-1]
        v[subscript] = value

    def _find_line(self, line_number):
        for index, possible in enumerate(self._program):
            if possible.line == line_number:
                return ControlLocation(index=index, offset=0)
        raise BasicSyntaxError(F"No line {line_number} found.")

    def goto_line(self, line):
        target = self._find_line(line)
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
        go_to = self._find_line(line_number)
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
        current_index = self._index
        current_offset = self._stmt_index
        current_offset += 1
        if current_offset >= len(self._program[current_index].stmts):
            current_index = self._program[current_index].next
            current_offset = 0
        return ControlLocation(current_index, current_offset)

    def _get_next_line(self):
        next_index = self._program[self._index].next
        if next_index is None:
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
            self._run = False
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


