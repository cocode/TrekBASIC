"""
This module contains the code the execute BASIC commands, and the class
that runs the program (Executor)
"""
from enum import Enum

from trekbasicpy.basic_dialect import DIALECT
from trekbasicpy.basic_interpreter import Executor
from trekbasicpy.basic_parsing import (
    ParsedStatement, ParsedStatementData, ParsedStatementDef, ParsedStatementDim, ParsedStatementElse, ParsedStatementFor, ParsedStatementGo, ParsedStatementIf, ParsedStatementInput, ParsedStatementLet, ParsedStatementNext, ParsedStatementNoArgs, ParsedStatementOnGoto, ParsedStatementPrint, ParsedStatementRead, ParsedStatementRem, ParsedStatementRestore, ParsedStatementThen, ParsedStatementTrace
)
from trekbasicpy.basic_types import BasicRuntimeError, BasicSyntaxError, RunStatus, SymbolType, assert_syntax, \
    is_valid_identifier, is_line_number
from trekbasicpy.basic_utils import TRACE_FILE_NAME
from trekbasicpy.basic_lexer import get_lexer
from trekbasicpy.basic_expressions import Expression


def stmt_rem(executor: Executor, stmt):
    """
    Does nothing.
    :return:
    """
    # TODO: Currently we tokenize past a rem statement, and consider them valid statements.
    # Need to fix that, but for now, just skip them
    executor.goto_next_line()


def stmt_print(executor: Executor, stmt: ParsedStatementPrint) -> None:
    """
    Executes a BASIC PRINT statement.
    """
    for i, arg in enumerate(stmt._outputs):
        if arg == ",":
            # BASIC comma separator — advance to next tab stop
            executor.do_print("\t", end='')  # This could be enhanced to simulate 14-column stops
            continue
        elif arg == ";":
            # BASIC semicolon separator — no extra spacing
            continue

        # Handle value (expression or string or concat group)
        if isinstance(arg, list):
            # Concatenated parts: e.g., "Hello" + A$
            for part in arg:
                if part.startswith('"') and part.endswith('"'):
                    executor.do_print(part[1:-1], end='')
                else:
                    v = eval_expression(executor._symbols, part)
                    if isinstance(v, (int, float)):
                        executor.do_print(f" {v:g} ", end='')  # space around numbers
                    else:
                        executor.do_print(str(v), end='')
        else:
            # Single string or expression
            if arg.startswith('"') and arg.endswith('"'):
                executor.do_print(arg[1:-1], end='')
            else:
                v = eval_expression(executor._symbols, arg)
                if isinstance(v, (int, float)):
                    executor.do_print(f" {v:g} ", end='')
                else:
                    executor.do_print(str(v), end='')

    if not stmt._no_cr:
        executor.do_print("")  # Final newline unless suppressed


def _handle_goto_gosub(executor, stmt: ParsedStatementGo, op_name: str, jump_func):
    """
    Common implementation for GOTO and GOSUB statements.
    
    :param executor: The executor instance
    :param stmt: The parsed GOTO/GOSUB statement
    :param op_name: The operation name for error messages ("GOTO" or "GOSUB")
    :param jump_func: The function to call for jumping (executor.goto_line or executor.gosub)
    """
    if hasattr(stmt, '_is_computed') and stmt._is_computed:
        # Handle computed GOTO/GOSUB (GOTO/GOSUB expr OF line1,line2,...)
        result = eval_expression(executor._symbols, stmt._expression)
        if not (type(result) == int or type(result) == float):
            raise BasicSyntaxError(f"Expression not numeric in {op_name}...OF")
        
        original_result = int(result)
        result = original_result - 1  # Basic is 1-based
        # Check if the index is out of range
        if result < 0 or result >= len(stmt._target_lines):
            raise BasicSyntaxError(f"{op_name} OF index {original_result} is out of range (1-{len(stmt._target_lines)})")
        
        # Execute the computed jump
        jump_func(stmt._target_lines[result])
    else:
        # Handle regular GOTO/GOSUB
        destination = stmt.destination
        assert_syntax(is_line_number(destination), F"{op_name} target is not an int ")
        jump_func(int(destination))


def stmt_goto(executor, stmt: ParsedStatementGo):
    _handle_goto_gosub(executor, stmt, "GOTO", executor.goto_line)
    return None


def stmt_gosub(executor, stmt: ParsedStatementGo):
    _handle_goto_gosub(executor, stmt, "GOSUB", executor.gosub)
    return None


def stmt_error(executor, stmt:ParsedStatement):
    raise Exception("THIS EXCEPTION IS EXPECTED. It is for testing.")


def stmt_for(executor, stmt: ParsedStatementFor):
    var = stmt._index_clause
    start = stmt._start_clause
    start = eval_expression(executor, start)
    is_valid_identifier(var)
    executor.put_symbol(var, start, SymbolType.VARIABLE, None)
    executor.do_for(var, stmt._to_clause, stmt._step_clause, executor.get_next_stmt())


def stmt_next(executor, stmt:ParsedStatementNext):
    index = stmt.loop_var
    var, to_clause, step_clause, loop_top = executor.do_next_peek(index)
    value = executor.get_symbol(var)
    to_value = eval_expression(executor._symbols, to_clause)
    step_value = eval_expression(executor._symbols, step_clause)
    value = value + step_value
    executor.put_symbol(var, value, SymbolType.VARIABLE, None)
    if value <= to_value:
        # Loop continues - goto loop top without popping
        executor._goto_location(loop_top)
    else:
        # Loop is done - pop the FOR record and continue to next statement
        executor.do_next_pop(var)


def is_string_variable(variable:str):
    return variable.endswith("$")



def assign_variable(executor, variable, value):
    """
    Variable assignment can include assigning array elements.
    :param variable:
    :param value:
    :return:
    """
    variable = variable.replace(" ", "")
    # TODO Should move parsing of this to ParsedStatementLet.
    # TODO Need to handle N-dimensional array element assignment.
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
    lexer = get_lexer()
    tokens = lexer.lex(value)
    e = Expression()
    result = e.eval(tokens, symbols=symbols)
    return result


def stmt_let(executor, stmt:ParsedStatementLet):
    result = stmt._expression.eval(stmt._tokens, symbols=executor._symbols)
    assign_variable(executor, stmt._variable, result)


def stmt_clear(executor, stmt):
    # Clear statement removes all variables.
    # Not to be confused with the CLEAR commannd in basic shell.
    executor.init_symbols()


def init_array(dimensions:list):
    if len(dimensions) == 1:
        return [0] * dimensions[0]
    one = []
    for x in range(dimensions[0]):
        one.append(init_array(dimensions[1:]))
    return one


def stmt_dim(executor, stmt:ParsedStatementDim):
    """
    Declares an array. Initializes it to zeros.

    TODO Handle more than two dimensions.
    :param executor:
    :param stmt:
    :return:
    """
    for name, dimension_expressions in stmt._dimensions:
        # Evaluate each dimension expression at runtime
        evaluated_dimensions = []
        for dim_expr in dimension_expressions:
            result = eval_expression(executor._symbols, dim_expr)
            evaluated_dimensions.append(int(result))
        # TODO put a limit on array size
        initializer = init_array(evaluated_dimensions)
        executor.put_symbol(name, initializer, SymbolType.ARRAY, arg=None)


def stmt_if(executor, stmt):
    """
    An "IF" statement works by skipping to the next line, if the THEN clause is false, otherwise
    it continues to execute the clauses after the THEN.
    :param executor:
    :param stmt:
    :return: None
    """
    e = Expression()
    result = e.eval(stmt._tokens, symbols=executor._symbols)
    if not result:
        executor.goto_else()    # Continue execution after the else statement.


def stmt_input(executor, stmt):
    for var in stmt._input_vars:
        is_valid_identifier(var)
    prompt = stmt._prompt
    # Not sure if this can be an expression. None are used in my examples, but why not?
    if prompt:
        # TODO If we add semicolon an an op that behaves like comma, multi-element prompts should work.
        prompt = eval_expression(executor._symbols, prompt)
    while True:
        if prompt:
            executor.do_print(prompt + " ", end='')
        else:
            executor.do_print("? ", end='')
        result = executor.do_input()
        if result is None:
            print("Bad response from trekbot")
            raise BasicRuntimeError(F"Bad response from trekbot")   # TODO This should not be in the core program,
                                                                    # TrekBot should be transparent
        result = result.split(",")
        if len(result) != len(stmt._input_vars):
            print(F"Mismatched number of inputs. Expected {len(stmt._input_vars)} got {len(result)}. Try Again.")
            continue

        for value, var in zip(result, stmt._input_vars):
            ok = False
            if not is_string_variable(var):
                try:
                    value = float(value)
                except Exception as e:
                    print("Invalid number. Try again.")
                    break
            else:
                if DIALECT.UPPERCASE_INPUT:
                    value = value.upper()

            executor.put_symbol(var, value, SymbolType.VARIABLE, None)
        else:
            break # Break the while, if we did NOT get an invalid number (break from for)



def stmt_on(executor, stmt):
    var = stmt._expression
    op = stmt._op
    result = eval_expression(executor._symbols, var)
    if not (type(result) == int or type(result) == float):
        raise BasicSyntaxError(f"Expression not numeric in ON GOTO/GOSUB")  # TODO We should catch this at load time.

    original_result = int(result)
    result = original_result - 1 # Basic is 1-based.
    # ON...GOTO/GOSUB should generate an error if the index is out of range
    if result < 0 or result >= len(stmt._target_lines):
        raise BasicSyntaxError(f"ON {op} index {original_result} is out of range (1-{len(stmt._target_lines)})")
    if op == "GOTO":
        executor.goto_line(stmt._target_lines[result])
    elif op == "GOSUB":
        executor.gosub(stmt._target_lines[result])
    else:
        assert_syntax(False, "Bad format for ON statement.")


def stmt_end(executor, stmt):
    executor._run = RunStatus.END_CMD

def stmt_else(executor, stmt):
    executor.goto_next_line()

def stmt_then(executor, stmt):
    pass

def stmt_stop(executor, stmt):
    print("Stopping program")
    executor._run = RunStatus.END_STOP

def stmt_trace(executor, stmt):
    print("starting tracing program") # TODO just for debugging, then delete this line,
    f = open(TRACE_FILE_NAME, "a")
    # There's a close on program exit()
    executor.set_trace_file(f)

def stmt_def(executor, stmt:ParsedStatementDef):
    """
    Define a user-defined function.

    470 DEF FND(D)=SQR((K(I,1)-S1)^2+(K(I,2)-S2)^2)

    :param executor:
    :param stmt:
    :return:
    """
    executor.put_symbol(stmt._variable, stmt._tokens, SymbolType.FUNCTION, stmt._function_arg)


def stmt_return(executor, stmt):
    executor.do_return()


def stmt_data(executor, stmt):
    """
    DATA statements are passive - they just hold data for READ statements.
    No execution needed.
    """
    pass


def stmt_read(executor, stmt):
    """
    Read data values from DATA statements and assign to variables.
    """
    from trekbasicpy.basic_parsing import ParsedStatementRead
    
    for var_name in stmt._variables:
        # Get the next data value
        try:
            data_value = executor.read_data_value()
        except BasicRuntimeError as e:
            # Re-raise with current line context
            raise BasicRuntimeError(str(e))
        
        # Determine if this is a string variable by checking the base variable name
        var_clean = var_name.replace(" ", "")
        i = var_clean.find("(")
        if i != -1:
            # Array element - check base variable name
            base_var = var_clean[:i]
            is_string_var = base_var.endswith("$")
        else:
            # Simple variable
            is_string_var = is_string_variable(var_name)
        
        # Convert data value to appropriate type based on variable type
        if is_string_var:
            # String variable - remove quotes if present
            if data_value.startswith('"') and data_value.endswith('"'):
                value = data_value[1:-1]  # Remove quotes
            else:
                value = data_value
        else:
            # Numeric variable - convert to number
            try:
                if '.' in data_value or 'E' in data_value.upper():
                    value = float(data_value)
                else:
                    value = int(data_value)
            except ValueError:
                raise BasicRuntimeError(f"I can't convert {data_value} to a number.")
        
        # Assign to variable (handles both simple variables and array elements)
        assign_variable(executor, var_name, value)


def stmt_restore(executor, stmt):
    """
    Reset the data pointer to beginning or to a specific line.
    """
    from trekbasicpy.basic_parsing import ParsedStatementRestore
    executor.restore_data(stmt._line_number)


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
    def __init__(self, execu, parser_class=ParsedStatement):
        self._parser = parser_class
        self._exec = execu

    def get_parser_class(self):
        return self._parser

    def get_exec(self):
        return self._exec


class Keywords(Enum):
    CLEAR = KB(stmt_clear, ParsedStatement) # Some uses of clear take arguments, which we ignore.
    DATA = KB(stmt_data, ParsedStatementData)
    DEF = KB(stmt_def, ParsedStatementDef) # User defined functions
    DIM = KB(stmt_dim, ParsedStatementDim)
    END = KB(stmt_end, ParsedStatementNoArgs)
    ELSE = KB(stmt_else, ParsedStatementElse)
    ERROR = KB(stmt_error, ParsedStatementNoArgs)
    FOR = KB(stmt_for, ParsedStatementFor)
    GOTO = KB(stmt_goto, ParsedStatementGo)
    GOSUB = KB(stmt_gosub, ParsedStatementGo)
    IF = KB(stmt_if, ParsedStatementIf)
    INPUT = KB(stmt_input, ParsedStatementInput)
    LET = KB(stmt_let, ParsedStatementLet)
    NEXT = KB(stmt_next, ParsedStatementNext)
    ON = KB(stmt_on, ParsedStatementOnGoto) # Computed gotos, gosubs
    PRINT = KB(stmt_print, ParsedStatementPrint)
    READ = KB(stmt_read, ParsedStatementRead)
    REM = KB(stmt_rem, ParsedStatementRem)
    RESTORE = KB(stmt_restore, ParsedStatementRestore)
    RETURN = KB(stmt_return, ParsedStatementNoArgs)
    STOP = KB(stmt_stop, ParsedStatementNoArgs) # Variant of END
    THEN = KB(stmt_then, ParsedStatementThen)
    TRACE = KB(stmt_trace, ParsedStatementTrace) # Trace program execution
    WIDTH = KB(stmt_width, ParsedStatement) # To support another version of superstartrek I found. Ignored

