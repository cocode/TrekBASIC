from collections import namedtuple
import sys

"""
Basic interpreter to run superstartrek.
"""

statement = namedtuple("Subs", "keyword args")
# Statements has a line number, and a list of statement.
statements = namedtuple("Statement", "line stmts next")
from enum import Enum, auto


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
def stmt_rem(program, stmt):
    """
    Does nothing.
    :return:
    """
    return None


def stmt_print(program, stmt):
    print(stmt.args[1:-1])
    return None

def stmt_for(program, stmt):
    raise Exception("Not implmented")

def stmt_exp(program, stmt):
    raise Exception("Not implmented")

class Keywords(Enum):
    EXP = stmt_exp,
    FOR = stmt_for,
    PRINT = stmt_print,
    REM = stmt_rem,


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
    s = statements(number, parsed, -1)
    return s


def tokenize(program_lines:list[str]) -> list[statements]:
    tokenized_lines = []
    for line in program_lines:
        tokenized_line = tokenize_line(line)
        tokenized_lines.append(tokenized_line)

    # Set default execution of next line.
    finished_lines = []
    if len(tokenized_lines): # Deal with zero length files.
        for i in range(len(tokenized_lines)-1):
            finished_lines.append(statements(tokenized_lines[i].line,
                                             tokenized_lines[i].stmts,
                                             i+1))
        finished_lines.append(tokenized_lines[-1])
    return finished_lines


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
    current = program[0]
    trace = False
    while run:
        if trace:
            print(F"{current.line}: ")
        # Get the statements on the current line
        stmts = current.stmts
        for s in stmts:
            if trace:
                print("\t", s.keyword, s.args)
            execution_function = s.keyword.value
            # Not sure why execution function is coming back a tuple
            execution_function[0](program, s)
            # TODO Handle goto, loops, and other control transfers
        if current.next != -1:
            current = program[current.next]
        else:
            run = False

def format_line(line):
    """
    Format a single line of the program. Should match the input exactly
    :param line:
    :return:
    """
    current = str(line.line) + " "
    for i in range(len(line.stmts)):
        if i:
            current += ":"
        stmt = line.stmts[i]
        if stmt.keyword == Keywords.EXP:
            name = ""
        else:
            name = stmt.keyword.name
        current += F"{name}{stmt.args}"
    return current


def format_program(program):
    lines = []
    for line in program:
        current = format_line(line)
        # current = str(line.line) + " "
        # for i in range(len(line.stmts)):
        #     if i:
        #         current += ":"
        #     stmt = line.stmts[i]
        #     if stmt.keyword == Keywords.EXP:
        #         name=""
        #     else:
        #         name = stmt.keyword.name
        #     current += F"{name}{stmt.args}"
        lines.append(current)
    return lines


def print_formatted(program, f = sys.stdout):
    lines = format_program(program)
    for line in lines:
        print(line)


if __name__ == "__main__":
    run_program("superstartrek.bas")
