"""
This module contains the code the load and parse BASIC programs
"""
from basic_find_str_quotes import find_next_str_not_quoted
from basic_types import ProgramLine, BasicSyntaxError, assert_syntax
from basic_utils import smart_split
from basic_statements import Keywords


def tokenize_statements(commands_text:list[str]):
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
                if list_of_statements[-1].keyword == Keywords.THEN and str.isdigit(command):
                    cmd = Keywords.GOTO

            parser_for_keyword = cmd.value.get_parser_class()
            parsed_statement = parser_for_keyword(cmd, command)

        list_of_statements.append(parsed_statement)

    return list_of_statements


def tokenize_line(program_line: str) -> ProgramLine:
    """
    Converts the line into a partially digested form. Tokenizing basic is mildly annoying,
    as there may not be a delimiter between the cmd and the args. Example:

    FORI=1TO8:FORJ=1TO8:K3=0:Z(I,J)=0:R1=RND(1)

    The FOR runs right into the I.

    So we need to prefix search.
    :param program_line:
    :return:
    """
    if len(program_line) == 0:
        return None

    # Get the line number
    try:
        number, partial = program_line.split(" ", 1)
    except ValueError as v:
        raise BasicSyntaxError("Syntax Error in: " + program_line) from v
    assert_syntax(str.isdigit(number), F"Invalid line number : {number} in {program_line}")
    number = int(number)
    # Parse the remainder of the line.
    list_of_statements = tokenize_remaining_line(partial, number)
    s = ProgramLine(number, list_of_statements, -1, source=program_line)
    return s


def add_colons(partial, target):
    """
    This function adds colons to a string, to simplify parsing.
    """
    offset = 0
    while (found := find_next_str_not_quoted(partial, target, offset) ) is not None:
        start, end = found
        partial = partial[:start] + ":" + target  + ":" + partial[end:]
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
    except ValueError as ve:
        # Annotate it with the line number and rethrow
        error = BasicSyntaxError(ve, line_number=number)
        raise error from ve
    return list_of_statements


def tokenize(program_lines:list[str]) -> list[ProgramLine]:
    tokenized_lines = []
    last_line: str = None
    for line_number, line in enumerate(program_lines):
        tokenized_line = tokenize_line(line)
        if tokenized_line is None:
            continue    # Ignore blank lines.
        if last_line is not None:
            assert_syntax(tokenized_line.line > last_line, F"Line {tokenized_line.line} is <= the preceding line {line}")
        tokenized_lines.append(tokenized_line)
        last_line = tokenized_line.line

    # Set default execution of next line.
    finished_lines = []
    if len(tokenized_lines): # Deal with zero length files.
        for i in range(len(tokenized_lines)-1):
            finished_lines.append(ProgramLine(tokenized_lines[i].line,
                                             tokenized_lines[i].stmts,
                                             i+1,
                                             source=tokenized_lines[i].source))
        finished_lines.append(ProgramLine(tokenized_lines[-1].line,
                                         tokenized_lines[-1].stmts,
                                         None,
                                         source=tokenized_lines[-1].source))
    return finished_lines


def load_program(program_filename) -> list[ProgramLine]:
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
