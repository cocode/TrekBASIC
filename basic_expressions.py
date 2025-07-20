"""
This module parses expressions
"""

from typing import List, Optional
from basic_types import lexer_token, BasicSyntaxError, assert_syntax
from basic_types import OP_TOKEN, UNARY_MINUS, ARRAY_ACCESS, SymbolType, UndefinedSymbol
from basic_symbols import SymbolTable

# =============================================================================
# CONSTANTS
# =============================================================================

# Special tokens used in expression evaluation
OPEN_PAREN = "("
CLOSE_PAREN = ")"
MINUS_OPERATOR = "-"

# Token types
TOKEN_TYPE_OPERATOR = "op"
TOKEN_TYPE_IDENTIFIER = "id"
TOKEN_TYPE_STRING = "str"
TOKEN_TYPE_NUMBER = "num"

# Maximum stack depth to prevent infinite recursion
MAX_STACK_DEPTH = 1000


class Expression:
    """
    A class for evaluating BASIC expressions using the Shunting Yard algorithm.
    
    This class converts infix expressions (like "2 + 3 * 5") to postfix notation
    and evaluates them using two stacks: one for operators and one for operands.
    It handles operator precedence, associativity, parentheses, unary operators,
    variables, arrays, and function calls.
    """

    def one_op(self, op_stack: List[OP_TOKEN], data_stack: List[lexer_token]) -> None:
        """
        Execute one operation from the operator stack.
        
        Pops an operator from the operator stack, evaluates it with operands
        from the data stack, and pushes the result back onto the data stack.
        
        Args:
            op_stack: Stack of operators waiting to be evaluated
            data_stack: Stack of operands and intermediate results
            
        Raises:
            BasicSyntaxError: If operator evaluation fails
        """
        from basic_operators import get_op

        assert_syntax(len(op_stack) > 0, "No operator to execute")
        
        current_operator = op_stack.pop()
        eval_class = get_op(current_operator)
        result = eval_class.eval(data_stack, op=current_operator)
        
        # Some operators (like parentheses) don't return a result
        if result is not None:
            data_stack.append(result)

    @staticmethod
    def get_type_from_name(current: lexer_token, tokens: List[lexer_token], token_index: int) -> SymbolType:
        """
        Determine whether an identifier is a variable, array, or function.
        
        Uses BASIC naming conventions and context to determine the symbol type:
        - Short names (1-2 chars, or 1-3 with $) followed by '(' are arrays
        - Short names not followed by '(' are variables  
        - Longer names are functions
        
        Args:
            current: The identifier token to analyze
            tokens: Complete list of tokens in the expression
            token_index: Current position in the token list
            
        Returns:
            SymbolType indicating VARIABLE, ARRAY, or FUNCTION
        """
        token_length = len(current.token)
        is_string_var = current.token.endswith('$')
        
        # Check BASIC variable name length constraints
        max_length = 3 if is_string_var else 2
        is_short_name = token_length <= max_length
        
        if is_short_name:
            # Short names: check if followed by '(' to distinguish array from variable
            has_following_paren = (token_index + 1 < len(tokens) and 
                                 tokens[token_index + 1].token == OPEN_PAREN)
            return SymbolType.ARRAY if has_following_paren else SymbolType.VARIABLE
        else:
            # Long names are functions
            return SymbolType.FUNCTION

    def _handle_operator(self, current_token: lexer_token, op_stack: List[OP_TOKEN], 
                        data_stack: List[lexer_token], is_unary_context: bool,
                        symbols: SymbolTable) -> bool:
        """
        Process an operator token in the expression.
        
        Handles operator precedence, unary minus detection, parentheses matching,
        and maintains the operator stack according to Shunting Yard algorithm.
        
        Args:
            current_token: The operator token to process
            op_stack: Stack of pending operators
            data_stack: Stack of operands and results
            is_unary_context: True if this position could have a unary operator
            symbols: Symbol table for variable/function lookups
            
        Returns:
            bool: New unary context state for next token
            
        Raises:
            BasicSyntaxError: On unbalanced parentheses or operator errors
        """
        from basic_operators import get_precedence
        
        # Handle unary minus: convert '-' to unary minus in unary context
        operator_token = current_token.token
        if operator_token == MINUS_OPERATOR and is_unary_context:
            current_token = lexer_token(UNARY_MINUS, current_token.type)
            operator_token = UNARY_MINUS

        # Process operators with higher or equal precedence from stack
        while len(op_stack) > 0:
            top_operator = op_stack[-1]
            
            # Left parenthesis acts as a precedence barrier
            if top_operator.token == OPEN_PAREN:
                break
                
            # Apply left associativity: equal precedence operators are evaluated left-to-right
            if get_precedence(lexer_token(top_operator.token, top_operator.type)) >= get_precedence(current_token):
                self.one_op(op_stack, data_stack)
            else:
                break

        # Handle closing parenthesis: pop until matching open parenthesis
        if operator_token == CLOSE_PAREN:
            assert_syntax(len(op_stack) > 0 and op_stack[-1].token == OPEN_PAREN, 
                         "Unbalanced parentheses: missing '('")
            op_stack.pop()  # Remove the matching '('
            return False  # After ')', we're not in unary context
        else:
            # Push operator onto stack (except closing parenthesis)
            op_stack.append(OP_TOKEN(operator_token, current_token.type, None, None, symbols=None))
            return True  # After operator, we're in unary context

    def _handle_identifier(self, current_token: lexer_token, tokens: List[lexer_token],
                          token_index: int, data_stack: List[lexer_token], 
                          op_stack: List[OP_TOKEN], symbols: SymbolTable) -> None:
        """
        Process an identifier (variable, array, or function) in the expression.
        
        Determines the symbol type, validates it exists, and either pushes its value
        to the data stack (for variables) or pushes a function/array operation to 
        the operator stack.
        
        Args:
            current_token: The identifier token to process
            tokens: Complete list of tokens in the expression
            token_index: Current position in the token list  
            data_stack: Stack of operands and results
            op_stack: Stack of pending operators
            symbols: Symbol table for variable/function lookups
            
        Raises:
            UndefinedSymbol: If the identifier is not defined
            BasicSyntaxError: On symbol type mismatches
        """
        symbol_type = Expression.get_type_from_name(current_token, tokens, token_index)

        # Validate symbol exists
        if not symbols.is_symbol_defined(current_token.token, symbol_type):
            raise UndefinedSymbol(f"Undefined variable: '{current_token.token}'")

        symbol_value = symbols.get_symbol(current_token.token, symbol_type)
        actual_symbol_type = symbols.get_symbol_type(current_token.token, symbol_type)
        
        # Verify our type determination matches symbol table
        assert symbol_type == actual_symbol_type, f"Symbol type mismatch for {current_token.token}"

        if symbol_type == SymbolType.VARIABLE:
            # Variables: push value directly to data stack
            if current_token.token.endswith("$"):
                data_stack.append(lexer_token(symbol_value, TOKEN_TYPE_STRING))
            else:
                data_stack.append(lexer_token(symbol_value, TOKEN_TYPE_NUMBER))
                
        elif symbol_type == SymbolType.FUNCTION:
            # Functions: push as operator for later evaluation
            function_arg = symbols.get_symbol_arg(current_token.token, SymbolType.FUNCTION)
            op_stack.append(OP_TOKEN(current_token.token, SymbolType.FUNCTION, 
                                   function_arg, symbol_value, symbols=symbols))
        else:
            # Arrays: push array access operation
            array_name = current_token.token
            op_stack.append(OP_TOKEN(ARRAY_ACCESS, "array_access", 
                                   array_name, None, symbols=symbols))

    def _process_remaining_operators(self, op_stack: List[OP_TOKEN], 
                                   data_stack: List[lexer_token]) -> None:
        """
        Process all remaining operators on the stack after parsing is complete.
        
        This is the final phase of the Shunting Yard algorithm where all
        remaining operators are popped and evaluated.
        
        Args:
            op_stack: Stack of remaining operators
            data_stack: Stack of operands and results
            
        Raises:
            BasicSyntaxError: If there are unmatched parentheses or invalid expressions
        """
        while len(op_stack) > 0:
            # Check for unmatched opening parentheses
            if op_stack[-1].token == OPEN_PAREN:
                raise BasicSyntaxError("Unbalanced parentheses: missing ')'")
            self.one_op(op_stack, data_stack)

    def eval(self, tokens: List[lexer_token], *, symbols: Optional[SymbolTable] = None) -> lexer_token:
        """
        Evaluate a BASIC expression using the Shunting Yard algorithm.
        
        Converts an infix expression (like "2 + 3 * 5 - A + RND()") to postfix
        notation and evaluates it. Handles operator precedence, parentheses,
        unary operators, variables, arrays, and function calls.
        
        The algorithm uses two stacks:
        - Operator stack: holds operators and functions waiting for operands
        - Data stack: holds operands and intermediate results
        
        Args:
            tokens: List of lexer tokens representing the expression
            symbols: Symbol table containing variables, arrays, and functions.
                    If None, creates an empty table (mainly for testing).
                    
        Returns:
            lexer_token: The final result of the expression evaluation
            
        Raises:
            BasicSyntaxError: On malformed expressions, undefined variables, etc.
            UndefinedSymbol: When referencing undefined variables or functions
        """
        # Import here to avoid circular dependencies
        from basic_operators import get_op, get_precedence
        
        # Validate inputs
        if len(tokens) == 0:
            raise BasicSyntaxError("Empty expression")
            
        if symbols is None:
            symbols = SymbolTable()  # Create empty table for testing

        # Initialize stacks and state
        data_stack: List[lexer_token] = []
        op_stack: List[OP_TOKEN] = []
        is_unary_context = True  # Start in unary context (for expressions like "-5")
        
        # Process each token using Shunting Yard algorithm
        token_index = 0
        while token_index < len(tokens):
            current_token = tokens[token_index]
            
            # Prevent stack overflow
            if len(op_stack) > MAX_STACK_DEPTH or len(data_stack) > MAX_STACK_DEPTH:
                raise BasicSyntaxError("Expression too complex (stack overflow)")

            if current_token.type == TOKEN_TYPE_OPERATOR:
                # Process operators (including parentheses)
                is_unary_context = self._handle_operator(current_token, op_stack, data_stack, 
                                                       is_unary_context, symbols)
            elif current_token.type == TOKEN_TYPE_IDENTIFIER:
                # Process variables, arrays, and functions
                self._handle_identifier(current_token, tokens, token_index, 
                                      data_stack, op_stack, symbols)
                is_unary_context = False
            else:
                # Process literals (numbers, strings)
                data_stack.append(current_token)
                is_unary_context = False
                
            token_index += 1

        # Evaluate remaining operators
        self._process_remaining_operators(op_stack, data_stack)

        # Validate final state
        assert_syntax(len(op_stack) == 0, "Expression evaluation incomplete (operators remaining)")
        assert_syntax(len(data_stack) == 1, f"Expression evaluation error (expected 1 result, got {len(data_stack)})")

        return data_stack[0].token

