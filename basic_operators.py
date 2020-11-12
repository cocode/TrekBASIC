"""
Implementation for basic operators, such as add, subtract, etc.
"""
# TODO Unary Minus!


from enum import Enum, auto

from basic_types import lexer_token, assert_syntax, assert_internal
import basic_expressions
from basic_lexer import Lexer


class OP:
    def eval(self, stack, *, op):
        return None


class MONO_OP:
    def check_args(self, stack):
        assert_syntax(len(stack) >= 1, -1, "Not enough operands for binary operator")

    def eval1(self, first):
        return None

    def eval(self, stack, *, op):
        self.check_args(stack)
        first = stack.pop()
        answer = self.eval1(first.token, op=op)
        return lexer_token(answer, "num")

class FUNC_MONO_OP(MONO_OP):
    def eval1(self, first, *, op):
        e = basic_expressions.Expression()
        symbols = op.symbols.get_copy() # Have to get a new copy for each function execution,
                                        # More than one may use the same variable. x = fna(x)+fnb(x)
        symbols.put_symbol(op.arg, first, "variable", arg=None)
        lexer = Lexer()
        tokens = lexer.lex(op.value)
        result = e.eval(tokens, symbols=symbols)
        trace = False
        if trace:
            print(F"Function F({first})={op.value} returned", result)
        return result


class BINOP(OP):
    def check_args(self, stack):
        assert_syntax(len(stack) >= 2, -1, "Not enough operands for binary operator")

    def eval2(self, first, second):
        pass

    def eval(self, stack, *, op):
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
    FUNC = FUNC_MONO_OP()


def get_op(token:lexer_token, line):
    OP_MAP = {
        ")": Operators.CLOSE,
        "=": Operators.EQUALS,
        "-": Operators.MINUS,
        "+": Operators.PLUS,
        "/": Operators.DIV,
        "*": Operators.MUL,
        "^": Operators.EXP,
        "(": Operators.OPEN,
        "∫": Operators.FUNC  # Not found in source code, used as an indicator.
    }
    if token.type == "function" and token.token.startswith("FN"):
        return OP_MAP["∫"]
    op_char = token.token
    assert_internal(len(op_char) == 1, line, F"Unexpected operator {op_char}")
    assert_syntax(op_char in OP_MAP, line, "Invalid operator {op_char}")
    return OP_MAP[op_char]


def get_precedence(token:lexer_token, line):
    PREC_MAP = {
        "(": 8,
        "=": 1,
        "-": 2,
        "+": 3,
        "/": 4,
        "*": 5,
        "^": 6,
        ")": 0,
        "∫": 7, # Has to be lower than "OPEN", so we will eval the arguments, THEN call the func.
    }

    if token.type == "function" and token.token.startswith("FN"):
        return PREC_MAP["∫"]
    op_char = token.token
    assert_internal(len(op_char) == 1, line, F"Unexpected operator {op_char}")
    assert_syntax(op_char in PREC_MAP, line, "Invalid operator {op_char}")
    return PREC_MAP[op_char]

