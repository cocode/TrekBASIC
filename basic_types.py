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


def assert_syntax(value, line, message):
    if not value:
        raise BasicSyntaxError(F"SyntaxError in line {line}: {message}")


