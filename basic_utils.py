"""
Utility functions. No dependencies on other modules in this program are allowed.
"""
import sys


def _find_keyword_outside_strings(line, keyword, start_pos=0, enquote='"', dequote='"'):
    """
    Find the position of a keyword outside of string literals.
    Returns the position of the keyword, or -1 if not found.
    For BASIC, keywords can run into identifiers (e.g., IFA>0 means IF A>0)
    """
    quoted = False
    i = start_pos
    keyword_len = len(keyword)
    
    while i <= len(line) - keyword_len:
        c = line[i]
        if not quoted and c == enquote:
            quoted = True
            i += 1
            continue
        if quoted and c == dequote:
            quoted = False
            i += 1
            continue
        if not quoted and line[i:i+keyword_len] == keyword:
            # For BASIC, just check that we're not in the middle of another keyword
            # We don't require word boundaries since IFA>0 is valid (IF A>0)
            if i == 0 or not line[i-1].isalpha():
                return i
        i += 1
    return -1


def smart_split(line: str, *, enquote: str = '"', dequote: str = '"', split_char: str = ":") -> list[str]:
    """
    Split a line into separate statements, handling colons inside quotes and IF THEN ELSE structures.
    
    For IF THEN ELSE statements, the entire structure is kept as one unit:
    - IF condition THEN statements ELSE statements
    
    :param line: The line to split
    :param enquote: The open quote character
    :param dequote: The close quote character  
    :param split_char: The character to split on, if not in quotes
    :return: List of statement strings
    """
    if split_char != ":":
        # For non-colon splitting (like comma splitting), use the original logic
        stuff = []
        quoted = False
        start = 0
        for x in range(len(line)):
            c = line[x]
            if not quoted and c == enquote:
                quoted = True
                continue
            if quoted and c == dequote:
                quoted = False
                continue
            if not quoted and c == split_char:
                stuff.append(line[start:x])
                start = x + 1
        if start < len(line):
            stuff.append(line[start:x+1])
        return stuff
    
    # Enhanced logic for colon splitting with IF THEN ELSE support
    
    # First, check if there's an IF statement
    if_pos = _find_keyword_outside_strings(line, "IF", 0, enquote, dequote)
    if if_pos == -1:
        # No IF statement, use regular colon splitting
        stuff = []
        quoted = False
        start = 0
        for x in range(len(line)):
            c = line[x]
            if not quoted and c == enquote:
                quoted = True
                continue
            if quoted and c == dequote:
                quoted = False
                continue
            if not quoted and c == split_char:
                stuff.append(line[start:x])
                start = x + 1
        if start < len(line):
            stuff.append(line[start:x+1])
        return stuff
    
    # Find THEN and ELSE positions
    then_pos = _find_keyword_outside_strings(line, "THEN", if_pos, enquote, dequote)
    if then_pos == -1:
        # No THEN found - this might be a malformed IF or IF might be part of another word
        # Fall back to regular colon splitting
        stuff = []
        quoted = False
        start = 0
        for x in range(len(line)):
            c = line[x]
            if not quoted and c == enquote:
                quoted = True
                continue
            if quoted and c == dequote:
                quoted = False
                continue
            if not quoted and c == split_char:
                stuff.append(line[start:x])
                start = x + 1
        if start < len(line):
            stuff.append(line[start:x+1])
        return stuff
    
    else_pos = _find_keyword_outside_strings(line, "ELSE", then_pos, enquote, dequote)
    
    if else_pos == -1:
        # IF THEN without ELSE - use original behavior
        stuff = []
        quoted = False
        start = 0
        for x in range(len(line)):
            c = line[x]
            if not quoted and c == enquote:
                quoted = True
                continue
            if quoted and c == dequote:
                quoted = False
                continue
            if not quoted and c == split_char:
                stuff.append(line[start:x])
                start = x + 1
        if start < len(line):
            stuff.append(line[start:x+1])
        return stuff
    else:
        # IF THEN ELSE - find where it ends
        # Look for the first colon after the ELSE clause
        colon_after_else = -1
        quoted = False
        for i in range(else_pos + 4, len(line)):
            c = line[i]
            if not quoted and c == enquote:
                quoted = True
                continue
            if quoted and c == dequote:
                quoted = False
                continue
            if not quoted and c == ':':
                colon_after_else = i
                break
        
        if colon_after_else == -1:
            # IF THEN ELSE goes to end of line
            return [line]
        else:
            # Split at the colon after IF THEN ELSE
            if_statement = line[:colon_after_else]
            remaining = line[colon_after_else + 1:]
            
            # Recursively split the remaining part
            remaining_parts = smart_split(remaining, enquote=enquote, dequote=dequote, split_char=split_char)
            
            return [if_statement] + remaining_parts


def format_line(line):
    """
    TODO: Compare this to the newer "format" in basic_shell.py. Maybe this is now redundant.
    Format a single line of the program.
    :param line:
    :return:
    """
    current = str(line.line) + " "
    for i in range(len(line.stmts)):
        if i:
            current += ":"
        stmt = line.stmts[i]
        name = stmt.keyword.name
        current += F"{name}{stmt.args}"
    return current


def format_program(program):
    lines = []
    for line in program:
        current = format_line(line)
        lines.append(current)
    return lines


def print_formatted(program, f = sys.stdout):
    lines = format_program(program)
    for line in lines:
        print(line)
