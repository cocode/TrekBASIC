"""
This selects between lexer implementations.
"""

from trekbasicpy.basic_dialect import DIALECT
import trekbasicpy.basic_lexer_long_var
import trekbasicpy.basic_lexer_old_style

# Available lexers mapped by name (uppercase)
_LEXER_MAP = {
    "OLD": trekbasicpy.basic_lexer_old_style.LexerOldStyle,
    "NEW": trekbasicpy.basic_lexer_long_var.LexerModernLongVar,
}

def set_lexer(option: str):
    global _selected
    key = option.upper()
    if key not in _LEXER_MAP:
        allowed = ", ".join(_LEXER_MAP.keys())
        raise ValueError(f"Unknown lexer option: '{option}'. Must be one of: {allowed}")
    _selected = key

def get_lexer():
    return _LEXER_MAP[DIALECT._lexer_selected]()