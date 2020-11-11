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
        :param symbols: The symbol table from the Executor
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
                    if get_precedence(top.token, line) > get_precedence(current.token, line): # Check operator precedence
                        top = op_stack.pop()
                        m = OP_MAP[top.token]  # An instance of OP
                        value = m.value
                        top_op_function = value[0]
                        result = top_op_function.eval(data_stack)
                        data_stack.append(result)
                    else:
                        break

                op_stack.append(tokens[token_index])
            else:
                data_stack.append(tokens[token_index])
            token_index += 1

        # Do anything left on the stack
        while len(op_stack):
            top = op_stack.pop()
            m = OP_MAP[top.token] # An instance of OP
            value = m.value
            top_op_function = value[0]
            result = top_op_function.eval(data_stack)
            data_stack.append(result)

        assert_syntax(len(op_stack) == 0, line, F"Expression not completed.")
        assert_syntax(len(data_stack) == 1, line, F"Data not consumed.")

        return data_stack[0].token

