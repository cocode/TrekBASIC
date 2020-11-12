"""
Implementation for basic operators, such as add, subtract, etc.
"""
# TODO Unary Minus!

from collections import namedtuple
import sys
from enum import Enum, auto

from basic_types import lexer_token, assert_syntax


class OP:
    def eval(self, stack):
        return None


class BINOP(OP):
    def check_args(self, stack):
        assert_syntax(len(stack) >= 2, -1, "Not enough operands for binary operator")

    def eval2(self, first, second):
        pass

    def eval(self, stack):
        self.check_args(stack)
        second = stack.pop()
        first = stack.pop()
        answer = self.eval2(first.token, second.token)
        return lexer_token(answer, "num")


class BINOP_NUM(BINOP):
    def check_args(self, stack):
        super().check_args(stack)
        assert_syntax(stack[-1].type == "num", -1, "Operand not numeric for binary op")
        assert_syntax(stack[-2].type == "num", -1, "Operand not numeric for binary op")

    def eval2(self, first:float, second:float):
        pass


class BINOP_STR_NUM(BINOP):
    """
    '+' is a special case, it can mean add, or it can mean string concatenation
    """
    def check_args(self, stack):
        super().check_args(stack)
        assert_syntax(stack[-1].type == "num" or stack[-1].type == "str", -1, "Operand not string or number for '+'")
        assert_syntax(stack[-2].type == "num" or stack[-2].type == "str", -1, "Operand not string or number for '+'")



class BINOP_MINUS(BINOP_NUM):
    def eval2(self, first, second):
        result = first- second
        return result


class BINOP_PLUS(BINOP_STR_NUM):
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
    CLOSE = OP() # NOP
    EQUALS = 2
    MINUS = BINOP_MINUS()
    PLUS = BINOP_PLUS()
    DIV = BINOP_DIV()
    MUL = BINOP_MUL()
    EXP = BINOP_EXP()
    OPEN = OP() # NOP


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
        "(": 7,
        "=": 1,
        "-": 2,
        "+": 3,
        "/": 4,
        "*": 5,
        "^": 6,
        ")": 0,
    }
    assert_syntax(op_char in PREC_MAP, line, "Invalid operator {op_char}")
    return PREC_MAP[op_char]

if __name__ == "__main__":
    pass
