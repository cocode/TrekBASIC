"""
Lexical analysis for the basic intrepreter.
"""

from collections import namedtuple
from enum import Enum, auto

UNARY_MINUS="—"# That's an m-dash.
ARRAY_ACCESS="@"

lexer_token = namedtuple("Token", "token type")
#statement = namedtuple("Subs", "keyword args")

# Statements has a line number, and a list of statement.
statements = namedtuple("Statement", "line stmts next")

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
