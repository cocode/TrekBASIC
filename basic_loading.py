"""
This module contains the code the load and parse BASIC programs
"""
from basic_types import ProgramLine, BasicSyntaxError, assert_syntax
from basic_utils import smart_split
from basic_statements import Keywords


def tokenize_statements(commands_text:list[str]):
    """
    Parses individual statements. A ine of the program may have multiple statements in it.

    This line has three statements.

    100 A=3:PRINT"A is equal to";A:X=6

    :param commands_text:
    :return:
    """
    list_of_statements = []
    options = [cmd for cmd in Keywords.__members__.values()]
    for command in commands_text:
        command = command.lstrip()
        for cmd in options:         # Can't just use a dict, because of lines like "100 FORX=1TO10"
            if command.startswith(cmd.name):
                parser_for_keyword = cmd.value.get_parser_class()
                parsed_statement = parser_for_keyword(cmd, command[len(cmd.name):])
                break
        else:
            # Assignment expression is the default
            cmd = Keywords.LET
            parser_for_keyword = cmd.value.get_parser_class()
            parsed_statement = parser_for_keyword(cmd, command)

        list_of_statements.append(parsed_statement)
        # This picks up the clauses after then "THEN" in an "IF ... THEN ..."
        additional_text = parsed_statement.get_additional()
        commands_array = smart_split(additional_text)
        for i in range(len(commands_array)):
            # Handle special case of "IF x THEN X=3:100"
            if commands_array[i].strip().isdigit():
                commands_array[i] = "GOTO "+commands_array[i]
        additional = tokenize_statements(commands_array)
        list_of_statements.extend(additional)

    return list_of_statements


def tokenize_line(program_line: str) -> ProgramLine:
    """
    Converts the line into a partially digested form. tokenizing basic is mildly annoying,
    as there may not be a delimiter between the cmd and the args. Example:

    FORI=1TO8:FORJ=1TO8:K3=0:Z(I,J)=0:R1=RND(1)

    The FOR runs right into the I.

    So we need to prefix search.
    :param program_line:
    :return:
    """
    if len(program_line) == 0:
        return None
    number, partial = program_line.split(" ", 1)
    assert_syntax(str.isdigit(number), F"Line number is not in correct format: {number}")
    number = int(number)

    # Rem commands don't split on colons, other lines do.
    if partial.startswith(Keywords.REM.name):
        commands_text = [partial]
    else:
        commands_text = smart_split(partial)
    try:
        list_of_statements = tokenize_statements(commands_text)
    except BasicSyntaxError as bse:
        print(F"Syntax Error in line {number}: {bse.message}: {program_line}")
        print()
        raise bse
    s = ProgramLine(number, list_of_statements, -1, source=program_line)
    return s


def tokenize(program_lines:list[str]) -> list[ProgramLine]:
    tokenized_lines = []
    last_line = None
    for line in program_lines:
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


def load_program(program_filename):
    """
    Loads and preprocesses a BASIC program.
    :param program_filename:  The filename to read the program from.
    :return: A tokenized program.
    """
    try:
        with open(program_filename) as f:
            lines = f.readlines()
    except FileNotFoundError as f:
        print(f)
        return
    lines = [line.strip() for line in lines]
    program = tokenize(lines)
    return program
