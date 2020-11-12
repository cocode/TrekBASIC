"""
Lexical analysis for the basic intrepreter.
"""

from collections import namedtuple
import sys
from enum import Enum, auto

from basic_types import lexer_token, BasicSyntaxError, assert_syntax

NUMBERS = "0123456789]"
LETTERS = "ABCDEGHIJKLMNOPQRSTUVWXYZ"
OPERATORS = "()^*/+-="


class Lexer:
    def __init__(self):
        pass

    def lex(self, text):
        state = None
        token = ""
        tokens = []
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
                    tokens.append(lexer_token(token, "id"))
                elif c in OPERATORS:
                    tokens.append(lexer_token(consume(), "op"))
                elif c in NUMBERS or c == '.':
                    token = ""
                    while (c := cur()) is not None and (c in NUMBERS or c == '.'):
                        token += consume()
                    tokens.append(lexer_token(float(token), "num"))
                elif c == '"':
                    consume()
                    token = ""
                    while (c := cur()) is not None and (c != '"'):
                        token += consume()
                    if cur() != '"':
                        raise BasicSyntaxError(F"No closing quote char.")
                    consume()
                    tokens.append(lexer_token(token, "str"))
                elif c == ' ' or c == '\t':
                    consume() # Ignore non quoted whitespace.
                else:
                    raise BasicSyntaxError(F"Unexpected char '{c}'")

        return tokens
