from collections import namedtuple

statement = namedtuple("Subs", "keyword args")
# Statements has a line number, and a list of statement.
statements = namedtuple("Statement", "line stmts")
from enum import Enum, auto


class Keywords(Enum):
    EXP = auto(),
    FOR = auto(),
    PRINT = auto(),
    REM = auto(),


def smart_split(line):
    """
    Colons split a line up into separate statements. But not if the colon is within quotes.

    :param input:
    :return:
    """

    stuff = []
    quoted = False
    start = 0
    for x in range(len(line)):
        c = line[x]
        if c == '"':
            if quoted:
                quoted = False
            else:
                quoted = True
        else:
            if not quoted and c == ":":
                stuff.append(line[start:x])
                start = x + 1
    if start < len(line):
        stuff.append(line[start:x+1])
    return stuff


# For now, don't tokenize in advance
def stmt_rem(line):
    return


def stmt_print(line_number:int, stmt, remainder):
    print(remainder)


def tokenize_line(program_line: object) -> statements:
    """
    Converts the line into a partially digested form. tokenizing basic is mildly annoying,
    as there may not be a delimiter between the cmd and the args. Example:

    FORI=1TO8:FORJ=1TO8:K3=0:Z(I,J)=0:R1=RND(1)

    The FOR runs right into the I.

    So we need to prefix search.
    :param program_line:
    :return:
    """
    number, partial = program_line.split(" ", 1)
    number = int(number)

    # Rem comands don't split on colons, other lines do.
    if partial.startswith(Keywords.REM.name):
        commands_text = [partial]
    else:
        commands_text = smart_split(partial)
    commands = []
    parsed = []
    options = [cmd for cmd in Keywords.__members__.values() if cmd.name != "EXP"]
    for command in commands_text:
        for cmd in options:
            if command.startswith(cmd.name):
                found = cmd
                args = command[len(cmd.name):]
                break
        else:
            found = Keywords.EXP
            args = command # No keyword at the front, so include all
        p = statement(found, args)
        parsed.append(p)
    s = statements(number, parsed)
    return s


def tokenize(program_lines:list[str]) -> list[statements]:
    tokenized_lines = []
    for line in program_lines:
        tokenized_line = tokenize_line(line)
        tokenized_lines.append(tokenized_line)
    return tokenized_lines


def interpret(lines):
    for line in lines:
        number, partial = line.split(" ", 1)
        print(number, partial)


def load_program(program_filename):
    with open(program_filename) as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    program = tokenize(lines)
    return program


def run_program(program_filename:str):
    program = load_program(program_filename)
    run = True
    while run:
        current = program[0]
        run = False


def format_program(program):
    lines = []
    for line in program:
        current = str(line.line) + " "
        for i in range(len(line.stmts)):
            if i:
                current += ":"
            stmt = line.stmts[i]
            if stmt.keyword == Keywords.EXP:
                name=""
            else:
                name = stmt.keyword.name
            current += F"{name}{stmt.args}"
        lines.append(current)
    return lines

def print_formatted(program):
    lines = format_program(program)
    for line in lines:
        print(line)

if __file__ == "__main__":
    run_program("superstartrek.bas")
