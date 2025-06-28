"""
Utility functions. No dependencies on other modules in this program are allowed.
"""
import sys


def smart_split(line:str, *, enquote:str = '"', dequote:str = '"', split_char:str = ":") -> list[str]:
    """
    Colons split up a line into separate statements. But not if the colon is within quotes.
    Adding comma split, for DIM G(8,8),C(9,2),K(3,3),N(3),Z(8,8),D(8)
    :param line:
    :param enquote: The open quote character.
    :param dequote: The close quote character.
    :param split_char: The character to split on, if not in quotes.
    :return:
    """

    stuff = []
    start = 0
    
    if enquote == dequote:
        # Simple case: quotes are the same (like "" for strings)
        # Use boolean flag
        quoted = False
        for x in range(len(line)):
            c = line[x]
            if c == enquote:
                quoted = not quoted
                continue
            if not quoted and c == split_char:
                stuff.append(line[start:x])
                start = x + 1
    else:
        # Complex case: quotes are different (like () for parentheses)
        # Use counter for nesting
        quote_depth = 0
        for x in range(len(line)):
            c = line[x]
            if c == enquote:
                quote_depth += 1
                continue
            if c == dequote:
                quote_depth -= 1
                continue
            if quote_depth == 0 and c == split_char:
                stuff.append(line[start:x])
                start = x + 1
    
    if start < len(line):
        stuff.append(line[start:len(line)])
    return stuff


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

TRACE_FILE_NAME="tracefile.txt"
