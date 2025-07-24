"""
This module contains the code the load and parse BASIC programs
"""
from typing import Optional

from trekbasicpy.basic_dialect import DIALECT
from trekbasicpy.basic_find_str_quotes import find_next_str_not_quoted
from trekbasicpy.basic_statements import Keywords
from trekbasicpy.basic_types import BasicSyntaxError, Program, ProgramLine, assert_syntax, is_line_number
from trekbasicpy.basic_utils import smart_split


def tokenize_statements(commands_text: list[str]):
    """
    Parses individual statements. A line of the program may have multiple statements in it.

    This line has three statements, separated by colons

    100 A=3:PRINT"A is equal to";A:X=6

        A=3
        PRINT"A is equal to";A
        X=6

    :param commands_text:
    :return:
    """
    list_of_statements = []
    options = [cmd for cmd in Keywords.__members__.values()]
    for command in commands_text:
        command = command.lstrip()
        command_upper = command.upper()
        for cmd in options:         # Can't just use a dict, because of lines like "100 FORX=1TO10"
            # Only use the uppercase version for lookup. Don't uppercase the whole statement.
            if command_upper.startswith(cmd.name):
                parser_for_keyword = cmd.value.get_parser_class()
                parsed_statement = parser_for_keyword(cmd, command[len(cmd.name):])
                break
        else:
            # Assignment expression is the default, unless you are following a THEN.
            # Following a THEN you can just have 100, for example. Short for goto 100
            cmd = Keywords.LET

            if list_of_statements:
                if list_of_statements[-1].keyword == Keywords.THEN and is_line_number(command):
                    cmd = Keywords.GOTO

            parser_for_keyword = cmd.value.get_parser_class()
            parsed_statement = parser_for_keyword(cmd, command)

        list_of_statements.append(parsed_statement)
        
        # If we hit a REM statement, everything after it is a comment
        if parsed_statement.keyword == Keywords.REM:
            break

    return list_of_statements


def tokenize_line(program_line: str) -> Optional[ProgramLine]:
    """
    Converts the line into a partially digested form. Tokenizing basic is mildly annoying,
    as there may not be a delimiter between the cmd and the args. Example:

    FORI=JTOK:FORJ=1TO8:K3=0:Z(I,J)=0:R1=RND(1)

    The FOR runs right into the I. "JTOK" for J TO K.

    So we need to do a prefix search.
    :param program_line:
    :return:
    """
    if len(program_line) == 0:
        return None

    # Get the line number
    number, partial = program_line.split(" ", 1)
    assert_syntax(is_line_number(number), F"Invalid line number : {number} in {program_line}")
    number = int(number)
    # Parse the remainder of the line.
    list_of_statements = tokenize_remaining_line(partial, number)
    s = ProgramLine(number, list_of_statements, source=program_line)
    return s


def add_colons(partial, target):
    """
    This function adds colons to a string, to simplify parsing.
    """
    offset = 0
    while (found := find_next_str_not_quoted(partial, target, offset)) is not None:
        start, end = found
        partial = partial[:start] + ":" + target + ":" + partial[end:]
        offset = end + 1
    return partial

def preprocess_then_else(source: str):
    """
    Breaks between statements are normally marked by a colon, but there are a couple of places the breaks are implied,
    and that's with THEN and ELSE.

    Rather than rewrite the whole parser (probably should be done), we are going to simply add a colon to mark
    the end of a statement explicitly.
    """
    a = add_colons(source, "else")
    b = add_colons(a, "then")
    return b

def tokenize_remaining_line(partial: str, number: int) -> list:
    """
    Tokenizes the string, but with the line number removed. This allows us to call this function with partial lines.
    """
    # Handle ! and ' comments - strip everything after comment markers (like some BASIC dialects)
    for comment_char in DIALECT.COMMENT_CHARS:
        comment_pos = find_next_str_not_quoted(partial, comment_char, 0)
        if comment_pos is not None:
            start, end = comment_pos
            partial = partial[:start].rstrip()  # Remove the comment and everything after it
            break  # Only process the first comment character found
    
    # Rem commands don't split on colons, other lines do.
    if partial.upper().strip().startswith(Keywords.REM.name):
        commands_text = [partial]
    else:
        preprocessed = preprocess_then_else(partial)
        commands_text = smart_split(preprocessed)
    try:
        list_of_statements = tokenize_statements(commands_text)
    except BasicSyntaxError as bse:
        # Annotate it with the line number and rethrow
        raise BasicSyntaxError(bse.message, number)
    return list_of_statements


def tokenize(program_lines: list[str]) -> Program:
    tokenized_lines = []
    last_line: Optional[str] = None
    for line_number, line in enumerate(program_lines):
        tokenized_line = tokenize_line(line)
        if tokenized_line is None:
            continue    # Ignore blank lines.
        if last_line is not None:
            assert_syntax(tokenized_line.line > last_line,
                          F"Line {tokenized_line.line} is <= the preceding line {line}")
        tokenized_lines.append(tokenized_line)
        last_line = tokenized_line.line

    # Return a Program object instead of manually managing next pointers
    return Program(tokenized_lines)


def load_program(program_filename) -> Program:
    """
    Loads and preprocesses a BASIC program.
    :param program_filename:  The filename to read the program from.
    :return: A tokenized program.
    """

    with open(program_filename) as f:
        lines = f.readlines()

    lines = [line.strip() for line in lines]
    program = tokenize(lines)
    return program
