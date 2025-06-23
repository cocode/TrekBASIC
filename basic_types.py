"""
Lexical analysis for the basic intrepreter.
"""

from collections import namedtuple
from enum import Enum, auto

UNARY_MINUS="—"# That's an m-dash.
ARRAY_ACCESS="@"

lexer_token = namedtuple("Token", "token type")
#statement = namedtuple("Subs", "keyword args")

# Represents one line in a basic program, which may be composed of multiple statements
# line: The line of the statement, "100" in "100 PRINT:PRINT:END"
# stmts: A list of statements
# next: This is an int that DOES NOT represent the line, it represents an index into the list of lines, or -1
#       for the last line.
# source: The original line as a str
ProgramLine = namedtuple("ProgramLine", "line stmts next source") # TODO Change "next" to "next_offset" for clarity.

# Symbol table entry
# Value - Value of the variable
# Type - SymbolType
# Arg - only used for SymbolType.FUNCTION. The X in DEF FNA(X)=X*X
ste = namedtuple("Symbol", "value type arg")


class BasicSyntaxError(Exception):
    def __init__(self, message, line_number=None):
        super().__init__(message)
        self.message = message
        self.line_number = line_number

class UndefinedSymbol(BasicSyntaxError):
    def __init__(self, message):
        super(UndefinedSymbol, self).__init__(message)
        self.message = message


class BasicInternalError(Exception):
    def __init__(self, message,):
        super(BasicInternalError, self).__init__(message)


def assert_syntax(value, message):
    if not value:
        raise BasicSyntaxError(F"SyntaxError: {message}")


def assert_internal(value, message):
    if not value:
        raise BasicInternalError(F"InternalError: {message}", line_number=-1)


# We had been using a lexical token for the operators, but function calls need more data.
# This what we will push on the op stack, and also pass to the eval function.
# arg, value, and exec are only required for user defined functions.
OP_TOKEN = namedtuple("OPERATION", "token type arg value symbols")


class SymbolType(Enum):
    VARIABLE = auto()
    FUNCTION = auto()
    ARRAY = auto()

# Records the ending status of the program.
class RunStatus(Enum):
    RUN=auto()          # Running normally
    END_CMD=auto()
    END_OF_PROGRAM=auto()
    END_ERROR_SYNTAX=auto()
    END_ERROR_INTERNAL=auto()
    BREAK_CODE=auto()
    BREAK_DATA=auto()
    BREAK_STEP=auto()


NUMBERS = "0123456789]"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


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
    assert_syntax(variable[1] in NUMBERS, F"Second char of '{variable}' must be a number or $.")
    if len(variable) == 2:
        return
    assert_syntax(variable[2] == '$', F"Invalid variable name {variable}")

def tokens_to_str(tokens:list[lexer_token]):
    s = ""
    for token in tokens:
        if token.type == "num" and int(token.token) == token.token:
            s += str(int(token.token))
        elif token.type == "str":
            s += '"' + token.token + '"'
        else:
            s += str(token.token)
    return s

