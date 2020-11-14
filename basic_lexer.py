"""
Lexical analysis for the basic intrepreter.
"""

from collections import namedtuple
import sys
from enum import Enum, auto

from basic_types import lexer_token, BasicSyntaxError, assert_syntax

NUMBERS = "0123456789]"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
OPERATORS = "()^*/+-=><"


class Lexer:
    def __init__(self):
        pass

    def lex(self, text):
        tokens = [token for token in self.lex2(text)]
        return tokens

    def lex2(self, text):
        state = None
        token = ""
        back = None
        index = 0

        def cur():
            if index == len(text):
                return None
            return text[index]

        def consume():
            nonlocal index
            current = text[index]
            index += 1
            return current # So we can get and consume in one operation.

        while (c := cur()) is not None:
            if state is None:
                if c in LETTERS:
                    token = ""
                    while (c := cur()) is not None and (c in LETTERS or c in NUMBERS or c == '$'):
                        token += consume()
                    yield lexer_token(token, "id")
                elif c in OPERATORS:
                    first = consume()
                    if cur() == ">":
                        consume()
                        yield lexer_token("<>", "op")
                    else:
                        yield lexer_token(first, "op")
                elif c in NUMBERS or c == '.':
                    token = ""
                    while (c := cur()) is not None and (c in NUMBERS or c == '.'):
                        token += consume()
                    yield lexer_token(float(token), "num")
                elif c == '"':
                    consume()
                    token = ""
                    while (c := cur()) is not None and (c != '"'):
                        token += consume()
                    if cur() != '"':
                        raise BasicSyntaxError(F"No closing quote char.")
                    consume()
                    yield lexer_token(token, "str")
                elif c == ' ' or c == '\t':
                    consume() # Ignore non quoted whitespace.
                else:
                    raise BasicSyntaxError(F"Unexpected char '{c}'")

        return
