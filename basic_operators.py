"""
Implementation for basic operators, such as add, subtract, etc.
"""
# TODO Unary Minus!
from collections import namedtuple
from enum import Enum
import random

from basic_types import lexer_token, assert_syntax, assert_internal, UNARY_MINUS, ARRAY_ACCESS

import basic_expressions
from basic_lexer import Lexer


class OP:
    def eval(self, stack, *, op):
        return None


class MONO_OP:
    def check_args(self, stack):
        assert_syntax(len(stack) >= 1, "Not enough operands for binary operator")

    def eval1(self, first, op):
        return None

    def eval(self, stack, *, op):
        self.check_args(stack)
        first = stack.pop()
        answer = self.eval1(first.token, op=op)
        return lexer_token(answer, "num")


class MINUS_MONO_OP(MONO_OP):
    def eval1(self, first, op):
        return -first


# TODO Basic allows for multiple arguments to a user defined function.
class FUNC_MONO_OP(MONO_OP):
    """
    handles user defined functions.
    """
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


# TODO Basic allows for multiple arguments to array subscripts
class ARRAY_ACCESS_MONO_OP(MONO_OP):
    """
    handles user defined functions.
    """
    def eval1(self, first, *, op):
        array_name = op.arg
        variable = op.symbols.get_symbol(array_name)
        variable_type = op.symbols.get_symbol_type(array_name)
        assert_syntax(variable_type == "array", "Array access to non-array variable '{variable}'")
        assert_syntax(int(first) == first, "Non-integral array subscript {first}'")
        return variable[int(first)] # TODO This will only work for one dimensional arrays, that don't have expressions as subscripts.



class FUNC_MONO_OP_INT(MONO_OP):
    """
    Handles the built-in INT function
    """
    def eval1(self, first, *, op):
        return int(first)

class ZERO_OP:
    def eval0(self):
        return None

    def eval(self, stack, *, op):
        answer = self.eval0()
        return lexer_token(answer, "num")


class FUNC_MONO_OP_RND(MONO_OP):
    """
    Handles the built-in RND function. I'm not certain what the behavior should be,
    I think he's always passing RND(1), and gets a number between 0 and 1.0. On some
    versions of BASIC RND(10) still generates from 0 to 1.0, on others in generate 0 to 10.0
    I'll assume always 1.0 for now.
    """
    def eval1(self, first, *, op):
        return random.random()

class HELPER: # Used by buildin functions.
    def __init__(self, x):
        self.value = x

class BINOP(OP):
    def check_args(self, stack):
        assert_syntax(len(stack) >= 2, "Not enough operands for binary operator")

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
        assert_syntax(stack[-1].type == "num", "Operand not numeric for binary op")
        assert_syntax(stack[-2].type == "num", "Operand not numeric for binary op")

    def eval2(self, first:float, second:float):
        pass


class BINOP_STR_NUM(BINOP):
    """
    '+' is a special case, it can mean add, or it can mean string concatenation
    """
    def check_args(self, stack):
        super().check_args(stack)
        assert_syntax(stack[-1].type == "num" or stack[-1].type == "str", "Operand not string or number for '+'")
        assert_syntax(stack[-2].type == "num" or stack[-2].type == "str", "Operand not string or number for '+'")



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

# TODO better data structures for operators.
alt_op = namedtuple('OperatorAlt','text precedence ltor func')
class Operators2(Enum):
    CLOSE = alt_op(")", 8, True, OP())
    EQUALS = 2
    MINUS = BINOP_MINUS()
    PLUS = BINOP_PLUS()
    DIV = BINOP_DIV()
    MUL = BINOP_MUL()
    EXP = BINOP_EXP()
    OPEN = OP() # NOP
    FUNC = FUNC_MONO_OP()
    UNARY_MINUS = MINUS_MONO_OP()


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
    UNARY_MINUS = MINUS_MONO_OP()
    ARRAY_ACCESS = ARRAY_ACCESS_MONO_OP()



def get_op(token:lexer_token):
    OP_MAP = {
        ")": Operators.CLOSE,
        "=": Operators.EQUALS,
        "-": Operators.MINUS,
        "+": Operators.PLUS,
        "/": Operators.DIV,
        "*": Operators.MUL,
        "^": Operators.EXP,
        "(": Operators.OPEN,
        "∫": Operators.FUNC,  # Not found in source code, used as an indicator.
        UNARY_MINUS: Operators.UNARY_MINUS,  # That's an m-dash.
        ARRAY_ACCESS: Operators.ARRAY_ACCESS,
    }
    if token.type == "function":# and token.token.startswith("FN"):
        if token.token == "INT":
            return HELPER(FUNC_MONO_OP_INT()) # Handles the built-in INT function
        if token.token == "RND":
            return HELPER(FUNC_MONO_OP_RND()) # Handles the built-in RND function
        return OP_MAP["∫"] # Handles user defined functions.
    op_char = token.token
    assert_internal(len(op_char) == 1, F"Unexpected operator {op_char}")
    assert_syntax(op_char in OP_MAP, "Invalid operator {op_char}")
    return OP_MAP[op_char]


def get_precedence(token:lexer_token):
    PREC_MAP = {
        "(": 9,
        "=": 1,
        "-": 2,
        "+": 3,
        "/": 4,
        "*": 5,
        "^": 6,
        ")": 0,
        "∫": 8, # Has to be lower than "OPEN", so we will eval the arguments, THEN call the func.
        UNARY_MINUS: 7, # Has to be lower than function calls (CLOSE) for "-FNA(X)" to work, and lower than array access
        ARRAY_ACCESS: 8,
    }

    if token.type == "function": # make this for all functions, not: and token.token.startswith("FN"):
        return PREC_MAP["∫"]
    op_char = token.token
    assert_internal(len(op_char) == 1, F"Unexpected operator {op_char}")
    assert_syntax(op_char in PREC_MAP, F"Invalid operator {op_char}")
    return PREC_MAP[op_char]

