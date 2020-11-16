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
# line: The line of the statement, 100 in 100 PRINT:PRINT:END
# stmts: A list of statements
# next: This is an int that DOES NOT represent the line, it represents an index into the list of lines, or -1
#       for the last line.
# TODO Rename to 'ProgramLine'
ProgramLine = namedtuple("ProgramLines", "line stmts next source") # TODO Change "next" to "next_offset" for clarity.

# Symbol table entry
# Value - Value of the variable
# Type - SymbolType
# Arg - only used for SymbolType.FUNCTION. The X in DEF FNA(X)=X*X
ste = namedtuple("Symbol", "value type arg")


class BasicSyntaxError(Exception):
    def __init__(self, message):
        super(BasicSyntaxError, self).__init__(message)
        self.message = message


class BasicInternalError(Exception):
    def __init__(self, message,):
        super(BasicInternalError, self).__init__(message)


def assert_syntax(value, message):
    if not value:
        raise BasicSyntaxError(F"SyntaxError: {message}")


def assert_internal(value, message):
    if not value:
        raise BasicInternalError(F"InternalError: {message}")


# We had been using a lexical token for the operators, but function calls need more data.
# This what we will push on the op stack, and also pass to the eval function.
# arg, value, and exec are only required for user defined functions.
OP_TOKEN = namedtuple("OPERATION", "token type arg value symbols")


class SymbolType(Enum):
    VARIABLE = auto()
    FUNCTION = auto()
    ARRAY = auto()
