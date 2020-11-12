"""
Basic support for expressions.
"""

from basic_types import lexer_token, BasicSyntaxError, assert_syntax, OP_TOKEN
from basic_symbols import SymbolTable


class Expression:
    def one_op(self, op_stack, data_stack, line):
        from basic_operators import get_op, get_precedence

        top = op_stack.pop()
        m = get_op(top, line)  # An instance of OP
        value = m.value
        top_op_function = value
        result = top_op_function.eval(data_stack, op=top)
        # Some operators, like parens, don't return a result
        if result is not None:
            data_stack.append(result)

    def eval(self, tokens:list[lexer_token], *, symbols=None, line=0):
        """
        evalulates an expression, like "2+3*5-A+RND()"
        :param symbols: a COPY!!! of the symbol table from the Executor
        :param tokens: the incoming list[lexer_token]
        :params line: The line number, for error messages only.
        :return:
        """
        from basic_operators import get_op, get_precedence # Import it in two places, so the IDE knows it's there.

        assert type(symbols) != dict
        # Had to iport here, to avoid circular dependencies.
        if symbols is None:
            symbols = SymbolTable()

        if len(tokens) == 0:
            raise BasicSyntaxError(F"No expression.")

        if len(tokens) == 1:
            assert_syntax(tokens[0].type != 'op', line, F"Invalid expression.")
            return tokens[0].token

        data_stack = []
        op_stack:OP_TOKEN = []
        token_index = 0
        while token_index < len(tokens):
            current = tokens[token_index]
            if current.type == "op":
                # Do anything on the stack that has higher precedence.
                while len(op_stack):
                    top = op_stack[-1]
                    # if top.type == 'function':
                    #     print("Found a function")
                    # This makes everything left associative. I think that's ok. Might be wrong for exponentiation
                    if top.token != "(" and get_precedence(top, line) >= get_precedence(current, line): # Check operator precedence
                        self.one_op(op_stack, data_stack, line)
                    else:
                        break
                if current.token != ")":
                    op_stack.append(OP_TOKEN(current.token, current.type, None, None, symbols=None))
                else:
                    assert_syntax(top.token == "(", line, F"Unbalanced parens.")
                    op_stack.pop()
            else:
                if current.type == "id":
                    assert_syntax(current.token in symbols.get_symbol_names(), line, F"Undefined variable: '{current.token}'")
                    symbol_value = symbols.get_symbol(current.token)
                    symbol_type = symbols.get_symbol_type(current.token)
                    if symbol_type == "variable":
                        if current.token.endswith("$"):
                            data_stack.append(lexer_token(symbol_value, "str"))
                        else:
                            data_stack.append(lexer_token(symbol_value, "num"))
                    elif symbol_type == "function":
                        # Handle function as operators. Lower priority than "(", but higher than everything else.
                        # So don't append this to the data stack, append it to the op stack as a function.
                        arg = symbols.get_symbol_arg(current.token)
                        fn_exp = Expression()
                        op_stack.append(OP_TOKEN(current.token, "function", arg, symbol_value, symbols=symbols))
                    else:
                        raise BasicSyntaxError(F"InternalError: Unknown symbol type: '{symbol_type}")
                else:
                    data_stack.append(current)
            token_index += 1

        # Do anything left on the stack
        while len(op_stack):
            self.one_op(op_stack, data_stack, line)

        assert_syntax(len(op_stack) == 0, line, F"Expression not completed.")
        assert_syntax(len(data_stack) == 1, line, F"Data not consumed.")

        return data_stack[0].token

