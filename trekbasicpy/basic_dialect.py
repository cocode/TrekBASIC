"""
Configuration constants for controlling BASIC dialect features.

This module defines switches that control various language features that vary 
between different dialects of BASIC. These settings allow the interpreter to 
emulate different BASIC variants by changing behavior for arrays, operators, 
input handling, etc. We expect to add more, as we support more programs.

All constants use UPPER_CASE naming following Python conventions for module-level constants.
"""
from dataclasses import dataclass

@dataclass
class BasicDialect(object):

    # =============================================================================
    # OPERATOR CONFIGURATION
    # =============================================================================

    # Operator used for exponentiation in mathematical expressions
    # Standard options: '^' (most common) or '**' (requires lexer changes)
    EXPONENTIATION_OPERATOR: str = '^'

    # =============================================================================
    # ARRAY CONFIGURATION
    # =============================================================================

    # Base index for array subscripts
    # 0 = Zero-based arrays (like C, Python): A(0) is first element
    # 1 = One-based arrays (traditional BASIC): A(1) is first element
    _ARRAY_OFFSET: int = 1

    # =============================================================================
    # INPUT/OUTPUT CONFIGURATION
    # =============================================================================

    # Controls whether user input is automatically converted to uppercase
    # 1 = Convert input to uppercase (traditional BASIC behavior)
    # 0 = Preserve the original case of the user input
    UPPERCASE_INPUT: int = 1

    # Characters that mark comment to the end of the line
    COMMENT_CHARS = ["!", "'"]

    # Current lexer
    _lexer_selected = "OLD"  # Default to legacy lexer

    # Other variants seen, that we don't yet support
    # automatic string conversion "ITEM #" + 1, vs. calling this an error.
    # implicit concatenation "hello"A$   # We have code for this, but it is not complete.
    # Does referencing an undefined numeric variable return 0, or throw an error?



DIALECT = BasicDialect()
