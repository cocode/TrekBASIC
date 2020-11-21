"""
This module contains the code the execute BASIC commands, and the class
that runs the program (Executor)
"""
from enum import Enum

from basic_dialect import UPPERCASE_INPUT
from basic_types import BasicSyntaxError, assert_syntax
from basic_types import SymbolType, RunStatus

from parsed_statements import ParsedStatement, ParsedStatementIf, ParsedStatementFor, ParsedStatementOnGoto
from parsed_statements import ParsedStatementInput
from basic_lexer import Lexer, NUMBERS, LETTERS
from basic_expressions import Expression
from basic_utils import smart_split

def stmt_rem(executor, stmt):
    """
    Does nothing.
    :return:
    """
    return None


def stmt_print(executor, stmt):
    """
    Prints output.
    :param executor: The program execution environment. Contains variables in its SymbolTable
    :param stmt: This print statement, contains parameters to the PRINT command.
    :return: None
    """
    arg = stmt.args.strip()
    if arg.endswith(";"):
        no_cr = True
    else:
        no_cr = False
    args = smart_split(arg, split_char=";")
    for i, arg in enumerate(args):
        arg = arg.strip()
        if len(arg) == 0:
            continue
        if arg[0] == '"': # quoted string
            assert_syntax(arg[0] =='"' and arg[-1] == '"', "String not properly quoted for 'PRINT'")
            output = arg[1:-1]
            output.replace(" ", "*") # TODO delete this line.
            executor.do_print(output, end='')
        else: # Expression
            v = eval_expression(executor._symbols, arg)
            #v = executor.get_symbol(arg)
            if type(v) == float:
                executor.do_print(F" {v:g} ", end='') # I'm trying to figure out BASIC's rules for spacing.
                                          # NO spaces is wrong (see initial print out)
                                          # Spaces around everything is wrong.
                                          # Spaces around numbers but not strings seems to work, so far.
            else:
                executor.do_print(F"{v}", end='')

    if not no_cr:
        executor.do_print("")
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


def stmt_error(executor, stmt:ParsedStatement):
    raise Exception("THIS EXCEPTION IS EXPECTED. It is for testing.")


def stmt_for(executor, stmt: ParsedStatementFor):
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
    """
    Declares an array. Initializes it to zeros.

    TODO Handle more than two dimensions.
    :param executor:
    :param stmt:
    :return:
    """
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
        elif len(dimensions) == 2:
            size_x = int(dimensions[0].replace("(",''))
            size_y = int(dimensions[1].replace(")",''))
            value = [ [0] * size_y for _ in range(size_x)] # wrong: [[0] * size_y] * size_x
        else:
            assert_syntax(False, F"Too many dimensions {len(dimensions)}")
        executor.put_symbol(name, value, SymbolType.ARRAY, arg=None) # Not right, but for now.


def stmt_if(executor, stmt):
    """
    An if statement works by skipping to the next line, if the THEN clause is false, otherwise
    it continues to execute the clauses after the THEN.
    :param executor:
    :param stmt:
    :return: None
    """
    lexer = Lexer()
    tokens = lexer.lex(stmt.args)
    e = Expression()
    result = e.eval(tokens, symbols=executor._symbols)
    if not result:
        executor.goto_next_line()


def stmt_input(executor, stmt):
    for var in stmt._input_vars:
        is_valid_identifier(var)
    prompt = stmt._prompt
    # Not sure if this can be an expression. None are used in my examples, but why not?
    if prompt:
        # TODO If we add semicolon an an op that behaves like comma, multi-element prompts should work.
        prompt = eval_expression(executor._symbols, prompt)
    executor.do_print(prompt, end='')
    result = executor.do_input()
    result = result.split(",")
    assert_syntax(len(result)== len(stmt._input_vars),
                  F"Mismatched number of inputs. Expected {len(stmt._input_vars)} got {len(result)}")
    for value, var in zip(result, stmt._input_vars):
        if not is_string_variable(var):
            value = float(value)
        else:
            if UPPERCASE_INPUT:
                value = value.upper()

        executor.put_symbol(var, value, SymbolType.VARIABLE, None)


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
    executor._run = RunStatus.END_CMD


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
        raise e
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


def stmt_width(executor, stmt):
    """
    The WIDTH statement is only for compatibility with some versions of BASIC. It set the width of the screen.

    Ignored.
    :param executor:
    :param stmt:
    :return:
    """
    pass


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
    ERROR = KB(stmt_error)
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
    WIDTH = KB(stmt_width) # To support another version of superstartrek I found. Ignored

