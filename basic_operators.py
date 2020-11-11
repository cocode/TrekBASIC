"""
Implementation for basic operators, such as add, subtract, etc.
"""
# TODO Unary Minus!

from collections import namedtuple
import sys
from enum import Enum, auto

from basic_interpreter import lexer_token, assert_syntax


class OP:
    def eval(self):
        pass


class BINOP(OP):
    def check_args(self, stack):
        assert_syntax(len(stack) >= 2, -1, "Not enough operands for binary operator")


class BINOP_NUM(BINOP):
    def check_args(self, stack):
        super().check_args(stack)

        assert_syntax(stack[-1].type == "num", -1, "Operand not numeric for binary op")
        assert_syntax(stack[-2].type == "num", -1, "Operand not numeric for binary op")

    def eval2(self, first:float, second:float):
        pass

    def eval(self, stack):
        self.check_args(stack)
        second = stack.pop()
        first = stack.pop()
        answer = self.eval2(first.token, second.token)
        return lexer_token(answer, "num")


class BINOP_MINUS(BINOP_NUM):
    def eval2(self, first, second):
        result = first- second
        return result


class BINOP_PLUS(BINOP_NUM):
    def eval2(self, first, second):
        result = first + second
        return result

class BINOP_MUL(BINOP_NUM):
    def eval2(self, first, second):
        result = first * second
        return result

class BINOP_DIV(BINOP_NUM):
    def eval2(self, first, second):
        result = first / second
        return result


class BINOP_EXP(BINOP_NUM):
    def eval2(self, first, second):
        result = first ** second
        return result


class Operators(Enum):
    CLOSE = 1,
    EQUALS = 2,
    MINUS = BINOP_MINUS(),
    PLUS = BINOP_PLUS(),
    DIV = BINOP_DIV(),
    MUL = BINOP_MUL(),
    EXP = BINOP_EXP(),
    OPEN = 3


OP_MAP = {
    ")": Operators.CLOSE,
    "=": Operators.EQUALS,
    "-": Operators.MINUS,
    "+": Operators.PLUS,
    "/": Operators.DIV,
    "*": Operators.MUL,
    "^": Operators.EXP,
    "(": Operators.OPEN
}


def get_precedence(op_char, line):
    PREC_MAP = {
        ")": 0,
        "=": 1,
        "-": 2,
        "+": 3,
        "/": 4,
        "*": 5,
        "^": 6,
        "(": 7
    }
    assert_syntax(op_char in PREC_MAP, line, "Invalid operator {op_char}")
    return PREC_MAP[op_char]

if __name__ == "__main__":
    pass
