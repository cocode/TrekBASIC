"""
Lexical analysis for the basic intrepreter.
"""

from collections import namedtuple
import sys
from enum import Enum, auto

from basic_types import lexer_token, BasicSyntaxError, assert_syntax

NUMBERS="0123456789]"
LETTERS="ABCDEGHIJKLMNOPQRSTUVWXYZ"
OPERATORS="()^*/+-="


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




class Executor:
    def __init__(self, program):
        self._program = program
        self._current = program[0]
        self._symbols = {}
        self._run = False

    def halt(self):
        self._run = False

    def run_program(self):
        #program = load_program(program_filename)
        self._run = True
        trace = False
        while self._run:
            if trace:
                print(F"{self._current.line}: ")
            # Get the statements on the current line
            stmts = self._current.stmts
            for s in stmts:
                if trace:
                    print("\t", s.keyword, s.args)
                execution_function = s.keyword.value
                # Not sure why execution function is coming back a tuple
                execution_function[0](self, s)
                # TODO Handle goto, loops, and other control transfers
            if self._current.next != -1:
                self._current = self._program[self._current.next]
            else:
                self._run = False

    def get_symbols(self):
        return self._symbols.copy()

    def put_symbol(self, symbol, value):
        self._symbols[symbol] = value

    def get_symbol(self, symbol):
        """
        This function is just for testing.
        :param symbol:
        :return:
        """
        return self._symbols[symbol]

