"""
Implementation for basic operators, such as add, subtract, etc.
"""

# TODO: Need to rewrite lexer to handle multi-character tokens for >=, <=



from collections import namedtuple
from enum import Enum
import random

from basic_dialect import ARRAY_OFFSET
from basic_types import lexer_token, assert_syntax, assert_internal, UNARY_MINUS, ARRAY_ACCESS, SymbolType

import basic_expressions
from basic_lexer import Lexer


class OP:
    def eval(self, stack, *, op):
        """
        Called to evaluate an operation in an expression.

        :param stack: The data stack, containing operand for the operation
        :param op: This is only used to provide context for user defined functions. TOOD: This should go into the symbol table
        :return:
        """
        return None


class MONO_OP:
    def __init__(self, lam=None):
        self._lambda = lam

    def check_args(self, stack):
        assert_syntax(len(stack) >= 1, "Not enough operands for binary operator")

    def eval1(self, first, op):
        if self._lambda:
            return self._lambda(first)

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
        symbols = op.symbols.get_nested_scope()
        symbols.put_symbol(op.arg, first, SymbolType.VARIABLE, arg=None)
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
        assert_syntax(variable_type == SymbolType.ARRAY, "Array access to non-array variable '{variable}'")
        assert_syntax(int(first) == first, "Non-integral array subscript {first}'")
        subscript = int(first) - ARRAY_OFFSET
        return variable[subscript] # TODO This will only work for one dimensional arrays, that don't have expressions as subscripts.


class BINOP(OP):
    def __init__(self, lam=None):
        self._lambda = lam

    def check_args(self, stack):
        assert_syntax(len(stack) >= 2, "Not enough operands for binary operator")

    def eval2(self, first, second):
        if self._lambda:
            return self._lambda(first, second)

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


class BINOP_STR_NUM(BINOP):
    """
    '+' is a special case, it can mean add, or it can mean string concatenation
    """
    def check_args(self, stack):
        super().check_args(stack)
        assert_syntax(stack[-1].type == "num" or stack[-1].type == "str", "Operand not string or number for '+'")
        assert_syntax(stack[-2].type == "num" or stack[-2].type == "str", "Operand not string or number for '+'")
        assert_syntax(stack[-1].type == stack[-2].type, "Operands don't match (string vs number) for '+'")


class BINOP_MINUS(BINOP_NUM):
    def eval2(self, first, second):
        result = first - second
        return result


OpDef = namedtuple('OpDef','text prec cls') # Later, might want to add associativity (L TO R or R TO L)

# If any additions, ALSO MUST UPDATE basic_lexer.py:OPERATORS. TODO Fix this.
class Operators(Enum):
    CLOSE=         OpDef(')',    0,  OP() )
    EQUALS=        OpDef('=',    1,  OP() )
    GT=            OpDef('>',    3,  BINOP_STR_NUM(lambda x, y: x > y))
    LT=            OpDef('<',    3,  BINOP_STR_NUM(lambda x, y: x < y))
    NE=            OpDef('<>',   3,  BINOP_STR_NUM(lambda x, y: x != y))
    # May be semantic differences between python "and" and basic "AND".
    # Python lets you AND to ints, basic does not. BINOP_BOOL maybe?
    # Basic only allows "AND" of booleans, I believe. TODO We should set the type
    # Of the output of a BOOLEAN and, and check that an IF only uses a BOOLEAN
    AND=           OpDef('AND',  2,  BINOP(lambda x, y: x and y) )
    OR=            OpDef('OR',   2,  BINOP(lambda x, y: x or y))
    MINUS=         OpDef('-',    4,  BINOP_NUM(lambda x, y: x - y))
    PLUS=          OpDef('+',    4,  BINOP_STR_NUM(lambda x, y: x + y))
    DIV=           OpDef('/',    5,  BINOP_NUM(lambda x, y: x / y))
    MUL=           OpDef('*',    5,  BINOP_NUM(lambda x, y: x * y))
    EXP=           OpDef('^',    6,  BINOP_NUM(lambda x, y: x ** y))
    OPEN=          OpDef('(',    9,  OP())
    FUNC=          OpDef('∫',    8,  FUNC_MONO_OP())
    UNARY_MINUS=   OpDef('—',    7,  MINUS_MONO_OP()) # M-dash
    ARRAY_ACCESS=  OpDef('@',    8,  ARRAY_ACCESS_MONO_OP())


OP_MAP={k.value.text:k for k in Operators}
OPERATORS = [k for k in OP_MAP] # TODO This is supposed to replace lexer.OPERATORS, but it's not done yet.

# Internal operations.
OPERATORS.remove(Operators.ARRAY_ACCESS.value.text)
OPERATORS.remove(Operators.FUNC.value.text)


def get_op_def(operator:str):
    assert_syntax(operator in OP_MAP, F"Invalid operator {operator}")
    return OP_MAP[operator].value


def get_op(token):
    """
    This gets the class that handles the operation. # TODO should change to "get_op_class"

    :param token: May be an OP_TOKEN, or a lexer_token # TODO Should subclass, maybe.
    :return: An instance of a class that handles that operation.
    """
    if token.type == SymbolType.FUNCTION:# and token.token.startswith("FN"):
        if token.token == "INT":
            return MONO_OP(lambda x: int(x)) # Handles the built-in INT function
        if token.token == "RND":
            return MONO_OP(lambda x: random.random()) # Handles the built-in RND function
        op_def = get_op_def("∫") # Handles user defined functions.
        return op_def.cls

    operator = token.token
    op_def = get_op_def(operator)
    return op_def.cls


def get_precedence(token:lexer_token):
    if token.type == SymbolType.FUNCTION: # make this for all functions, not: and token.token.startswith("FN"):
        return Operators.FUNC.value.prec # PREC_MAP["∫"]
    op_def = get_op_def(token.token)
    return op_def.prec

