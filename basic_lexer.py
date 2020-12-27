"""
This selects between lexer implementations.
"""

import basic_lexer1
import basic_lexer2


def get_lexer():
    if True:
        return basic_lexer1.Lexer()

    # This lexer is not working yet.
    return basic_lexer2.Lexer()
