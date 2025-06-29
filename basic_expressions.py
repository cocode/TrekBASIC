"""
Basic support for expressions.
"""

from basic_types import lexer_token, BasicSyntaxError, assert_syntax
from basic_types import OP_TOKEN, UNARY_MINUS, ARRAY_ACCESS, SymbolType, UndefinedSymbol
from basic_symbols import SymbolTable


class Expression:
    """
    A class for evaluating BASIC expressions. See evalI()
    """
    def one_op(self, op_stack, data_stack):
        """
        Perform one operation.
        :param op_stack: The operation stack, for example '*'
        :param data_stack: The operand stack.
        :return: None, it pushes the result back onto the data stack.
        """
        from basic_operators import get_op, get_precedence

        current_op = op_stack.pop()
        eval_class = get_op(current_op)
        result = eval_class.eval(data_stack, op=current_op)
        # Some operators, like parens, don't return a result
        if result is not None:
            data_stack.append(result)

    def get_type_from_name(self, current: lexer_token, tokens: list[lexer_token], token_index: int) -> SymbolType:
        if len(current.token) <= 2 or (current.token.endswith('$') and len(current.token) <= 3):
            if token_index + 1 < len(tokens) and tokens[token_index + 1].token == '(':
                symbol_type = SymbolType.ARRAY
            else:
                symbol_type = SymbolType.VARIABLE
        else:
            symbol_type = SymbolType.FUNCTION
        return symbol_type

    def eval(self, tokens:list[lexer_token], *, symbols=None) -> lexer_token:
        """
        Evaluates an expression, like "2+3*5-A+RND()"
        :param symbols: Symbols (BASIC variables) to use when evaluating the expression
        :param tokens: the incoming list[lexer_token]
        :return: A lexer token with the result and the type.
        """
        from basic_operators import get_op, get_precedence # Import it in two places, so the IDE knows it's there.
        # "-" is ambiguous. It can mean subtraction or unary minus.
        # if "-" follows a data item, it's subtraction.
        # if "-" follows an operator, it's unary minus, unless the operator is )
        # Why ")"? I need to be able to express this better.
        is_unary_context = True
        assert type(symbols) != dict
        if symbols is None: # Happens during testing.
            symbols = SymbolTable() # TODO Fix this. No "if test" allowed.

        if len(tokens) == 0:
            raise BasicSyntaxError(F"No expression.")

        data_stack = []
        op_stack:OP_TOKEN = []
        token_index = 0
        while token_index < len(tokens):
            current = tokens[token_index]

            if current.type == "op":
                if current.token == "-" and is_unary_context:
                    current = lexer_token(UNARY_MINUS, current.type)
                # Do anything on the stack that has higher precedence.
                while len(op_stack):
                    top = op_stack[-1]
                    # This makes everything left associative. I think that's ok. Might be wrong for exponentiation
                    # This says visual basic was left associative for everything.
                    # https://docs.microsoft.com/en-us/dotnet/visual-basic/language-reference/operators/operator-precedence
                    # This shows left associative exponentiation: (they use **, not ^)
                    # http://www.quitebasic.com/
                    if top.token != "(" and get_precedence(top) >= get_precedence(current): # Check operator precedence
                        self.one_op(op_stack, data_stack)
                    else:
                        break
                if current.token != ")":
                    op_stack.append(OP_TOKEN(current.token, current.type, None, None, symbols=None))
                else:
                    assert_syntax(top.token == "(", F"Unbalanced parens.")
                    op_stack.pop()
                if current.token == ")":
                    is_unary_context = False
                else:
                    is_unary_context = True
            else:
                if current.type == "id":
                    # TODO Problem: We now need to know the SymbolType of a variable to retrieve it
                    # but we don't know it here. Maybe we can defer referencing it, until it is
                    # used? At that point, we would know array vs function. I think.
                    # I think this works:
                    symbol_type = self.get_type_from_name(current, tokens, token_index)

                    if not symbols.is_symbol_defined(current.token, symbol_type):
                        raise UndefinedSymbol(F"Undefined variable: '{current.token}'")
                    symbol_value = symbols.get_symbol(current.token, symbol_type)
                    symbol_type2 = symbols.get_symbol_type(current.token, symbol_type)
                    # Changed the way that symbols tables work. Check that we are still consistent.
                    assert(symbol_type == symbol_type2)
                    if symbol_type == SymbolType.VARIABLE:
                        if current.token.endswith("$"):
                            data_stack.append(lexer_token(symbol_value, "str"))
                        else:
                            data_stack.append(lexer_token(symbol_value, "num"))
                    elif symbol_type == SymbolType.FUNCTION:
                        # Handle function as operators. Lower priority than "(", but higher than everything else.
                        # So don't append this to the data stack, append it to the op stack as a function.
                        arg = symbols.get_symbol_arg(current.token, SymbolType.FUNCTION)
                        op_stack.append(OP_TOKEN(current.token, SymbolType.FUNCTION, arg, symbol_value, symbols=symbols))
                    else:
                        # Array access
                        arg = current.token
                        op_stack.append(OP_TOKEN(ARRAY_ACCESS, "array_access", arg, None, symbols=symbols))
                else:
                    data_stack.append(current)
                is_unary_context = False
            token_index += 1

        # Do anything left on the stack
        while len(op_stack):
            self.one_op(op_stack, data_stack)

        assert_syntax(len(op_stack) == 0, F"Expression not completed.")
        assert_syntax(len(data_stack) == 1, F"Data not consumed.")

        return data_stack[0].token

