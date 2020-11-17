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
    def __init__(self, lam=None, return_type=None):
        self._lambda = lam
        self._return_type = return_type

    def check_args(self, stack):
        assert_syntax(len(stack) >= 1, "Not enough operands for binary operator")

    def eval1(self, first, op):
        if self._lambda:
            return self._lambda(first)

    def eval(self, stack, *, op):
        self.check_args(stack)
        first = stack.pop()
        answer = self.eval1(first.token, op=op)
        return_type = self._return_type if self._return_type is not None else first.type
        return lexer_token(answer, return_type)


class STR_OP(MONO_OP):
    """
    Base class for the string operations. LEFT$, MID$, RIGHT$
    """
    def __init__(self, lam, name, arg_count, return_type=None):
        """
        :param lam: A function that executes this command
        :param name: Just for debugging and error messages.
        :param arg_count: The number of arguments the function takes.
        :param return_type: The return type of eval(). If None, uses the type of the first argument.
        """
        super().__init__(lam=lam, return_type=return_type)
        self._name = name
        self._arg_count = arg_count

    def check_args(self, stack):
        super().check_args(stack)
        # Functions get their arguments in an array of parameters
        args = stack[-1].token
        if not isinstance(args, list):
            # Right now, function args are delivered in a list, only if there is more than one. TODO
            args = [args]
        assert_syntax(len(args) == self._arg_count, F"Wrong number of arguments {len(args)} for {self._name}")
        assert_syntax(isinstance(args[0], str), "First operand of {self._name} must be a string.")
        if self._arg_count >= 2:
            is_number = isinstance(args[1], int) or isinstance(args[1], float)
            assert_syntax(is_number, "Second operand of {self._name} must be a number.")
        if self._arg_count == 3:
            is_number = isinstance(args[2], int) or isinstance(args[2], float)
            assert_syntax(is_number, "Third operand of {self._name} must be a number.")

    def eval1(self, first, op):
        if self._lambda:
            return self._lambda(first)


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
        v = variable
        assert_syntax(variable_type == SymbolType.ARRAY, "Array access to non-array variable '{variable}'")
        if type(first) == list:
            # Multidimensional array access
            args = [int(arg)-ARRAY_OFFSET for arg in first] # TODO check type and syntax error. No strings, no arrays

            v = variable
            for arg in args:
                assert_syntax(type(v) is list, "Too many array dimensions for {array_name} subscript.")
                assert_syntax(arg < len(v), "Array subscript out of bounds for {array_name}")
                v = v[arg]
            return v
        else:
            # TODO should only need the above.
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
        return lexer_token(answer, first.type)


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
        assert_syntax(stack[-1].type == "num" or stack[-1].type == "str", "Operand not string or number.'")
        assert_syntax(stack[-2].type == "num" or stack[-2].type == "str", "Operand not string or number.")
        assert_syntax(stack[-1].type == stack[-2].type, "Operands don't match (string vs number) for '+'")


class BINOP_COMMA(BINOP):
    def eval2(self, first, second):
        if type(first) is not list:
            first = [first]

        if type(second) is list:
            first.extend(second)
        else:
            first.append(second)

        return first


OpDef = namedtuple('OpDef','text prec cls') # Later, might want to add associativity (L TO R or R TO L)

# If any additions, ALSO MUST UPDATE basic_lexer.py:OPERATORS. TODO Fix this.
class Operators(Enum):
    CLOSE=         OpDef(')',    0,  OP() )
    COMMA=         OpDef(',',    0.5,  BINOP_COMMA() )
    EQUALS=        OpDef('=',    1,  BINOP_STR_NUM(lambda x, y: x == y) ) # BOOLEAN =
    GT=            OpDef('>',    3,  BINOP_STR_NUM(lambda x, y: x > y))
    GTE=           OpDef('>=',   3,  BINOP_STR_NUM(lambda x, y: x >= y))
    LT=            OpDef('<',    3,  BINOP_STR_NUM(lambda x, y: x < y))
    LTE=           OpDef('<=',   3,  BINOP_STR_NUM(lambda x, y: x <= y))
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
OPERATORS2 = [k for k in OP_MAP] # TODO This is supposed to replace lexer.OPERATORS, but it's not done yet.

# Internal operations.
OPERATORS2.remove(Operators.ARRAY_ACCESS.value.text)
OPERATORS2.remove(Operators.FUNC.value.text)
OP_FIRST_CHAR=[a[0] for a in OPERATORS2]

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
        # To add another internal function.
        # 1. Add it here.
        # 2. Add it to basic_lexer.BUILT_IN_FUNCTIONS
        # 3. Add it to the list of internal functions in basic_interpreter.Executor.run_program
        if token.token == "INT":
            return MONO_OP(lambda x: int(x)) # Handles the built-in INT function # TODO we also define the functions in Excutor.
        if token.token == "RND":
            return MONO_OP(lambda x: random.random()) # Handles the built-in RND function
        if token.token == "LEFT$":
            return STR_OP(lambda x: x[0][:int(x[1])], token.token, 2)
        if token.token == "RIGHT$":
            return STR_OP(lambda x: x[0][-int(x[1]):], token.token, 2)
        if token.token == "MID$":
            return STR_OP(lambda x: x[0][int(x[1])-1:int(x[1])-1+int(x[2])], token.token, 3)
        if token.token == "LEN":
            return STR_OP(lambda x: len(x), token.token, 1, "num") # This needs to return an int, unlike the other str functions.
        if token.token == "SGN":
            return MONO_OP(lambda x: (x > 0) - (x < 0)) # Handles the built-in SGN function
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

