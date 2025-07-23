import re
from functools import lru_cache
from typing import Optional, Tuple

@lru_cache(maxsize=8)
def _compile_pattern(target: str):
    esc = re.escape(target)
    return re.compile(rf'^(?:[^"]*"[^"]*?")*?[^"]*?({esc})', flags=re.IGNORECASE)

def find_next_str_not_quoted(
    source: str,
    target: str,
    offset: int = 0,
) -> Optional[Tuple[int, int]]:
    """
    Returns (start, end) of the first occurrence of `target` in `source`
    that lies outside any double-quoted substrings, or None.
    """
    pattern = _compile_pattern(target)
    source = source[offset:]
    m = pattern.match(source)
    if not m:
        return None
    return m.start(1)+offset, m.end(1)+offset

