"""
Lexical analysis for the basic intrepreter.
"""

from collections import namedtuple
import sys
from enum import Enum, auto

lexer_token = namedtuple("Token", "token type")
statement = namedtuple("Subs", "keyword args")
# Statements has a line number, and a list of statement.
statements = namedtuple("Statement", "line stmts next")
# Symbol table entry
# Value - Value of the variable
# Type - "function", "variable"
# Arg - only used for "function". The X in DEF FNA(X)=X*X
ste = namedtuple("Symbol", "value type arg")


class BasicSyntaxError(Exception):
    def __init__(self, message,):
        super(BasicSyntaxError, self).__init__(message)


class BasicInternalError(Exception):
    def __init__(self, message,):
        super(BasicInternalError, self).__init__(message)


def assert_syntax(value, line, message):
    if not value:
        raise BasicSyntaxError(F"SyntaxError in line {line}: {message}")


def assert_internal(value, line, message):
    if not value:
        raise BasicInternalError(F"InternalError in line {line}: {message}")


# We had been using a lexical token for the operators, but function calls need more data.
# This what we will push on the op stack, and also pass to the eval function.
# arg, value, and exec are only required for user defined functions.
OP_TOKEN = namedtuple("OPERATION", "token type arg value symbols")
