"""
Basic support for expressions.
"""
from collections import namedtuple
import sys
from enum import Enum, auto
from basic_types import lexer_token, BasicSyntaxError, assert_syntax
from basic_operators import Operators, OP_MAP, get_precedence


class Expression:
    def eval(self, symbols, tokens:list[lexer_token], line):
        """
        evalulates an expression, like "2+3*5-A+RND()"
        :param symbols: a COPY!!! of the symbol table from the Executor
        :param tokens: the incoming list[lexer_token]
        :params line: The line number, for error messages only.
        :return:
        """
        if len(tokens) == 0:
            raise BasicSyntaxError(F"No expression.")

        if len(tokens) == 1:
            assert_syntax(tokens[0].type != 'op', line, F"Invalid expression.")
            return tokens[0].token

        data_stack = []
        op_stack = []
        token_index = 0
        while token_index < len(tokens):
            current = tokens[token_index]
            if current.type == "op":
                # Do anything on the stack that has higher precedence.
                while len(op_stack):
                    top = op_stack[-1]
                    # This makes everything left associative. I think that's ok. Might be wrong for exponentiation
                    if top.token != "(" and get_precedence(top.token, line) >= get_precedence(current.token, line): # Check operator precedence
                        top = op_stack.pop()
                        m = OP_MAP[top.token]  # An instance of OP
                        value = m.value
                        top_op_function = value
                        result = top_op_function.eval(data_stack)
                        # Some operators, like parens, don't return a result
                        if result is not None:
                            data_stack.append(result)
                    else:
                        break
                if current.token != ")":
                    op_stack.append(current)
                else:
                    assert_syntax(top.token=="(", line, F"Unbalanced parens.")
                    op_stack.pop()
            else:
                if current.type == "id":
                    # If it's a symbol, look it up, and replace with it's value.
                    assert_syntax(current.token in symbols, line, F"Undefined variable: '{current.token}")
                    entry = symbols.get(current.token)
                    symbol_type = entry.type
                    if symbol_type == "variable":
                        value = entry.value
                        if current.token.endswith("$"):
                            data_stack.append(lexer_token(value, "str"))
                        else:
                            data_stack.append(lexer_token(value, "num"))
                    elif symbol_type == "function":
                        pass
                        # value = entry.value
                        # arg = entry.arg
                        # fn_exp = Expression()
                        # local_symbols = symbols.copy() # Way inefficient, but easy
                        # local_symbols[arg]=symbols.get[]
                    else:
                        raise BasicSyntaxError(F"InternalError: Unknown symbol type: '{symbol_type}")
                else:
                    data_stack.append(current)
            token_index += 1

        # Do anything left on the stack
        while len(op_stack):
            top = op_stack.pop()
            m = OP_MAP[top.token] # An instance of OP
            value = m.value
            top_op_function = value
            result = top_op_function.eval(data_stack)
            if result is not None:
                data_stack.append(result)

        assert_syntax(len(op_stack) == 0, line, F"Expression not completed.")
        assert_syntax(len(data_stack) == 1, line, F"Data not consumed.")

        return data_stack[0].token

