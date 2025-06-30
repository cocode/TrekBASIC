import re
from typing import Optional, Tuple

def find_next_str_not_quoted(
    source: str,
    target: str,
    offset: int = 0,
) -> Tuple[Optional[int], Optional[int]]:
    """
    Returns (start, end) of the first occurrence of `target` in `source`
    that lies outside any double-quoted substrings, or (None, None).
    """
    esc = re.escape(target)
    pattern = re.compile(
        rf'^(?:[^"]*"[^"]*?")*?[^"]*?({esc})', flags=re.IGNORECASE
    )
    source = source[offset:]
    m = pattern.match(source)
    if not m:
        return None
    return m.start(1)+offset, m.end(1)+offset

