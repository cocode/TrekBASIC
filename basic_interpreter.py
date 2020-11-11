from collections import namedtuple
import sys

"""
Basic interpreter to run superstartrek.
"""

statement = namedtuple("Subs", "keyword args")
# Statements has a line number, and a list of statement.
statements = namedtuple("Statement", "line stmts next")
from enum import Enum, auto


def smart_split(line, enquote='"', dequote = '"', split_char=":"):
    """
    Colons split a line up into separate statements. But not if the colon is within quotes.
    Adding comma split, for DIM G(8,8),C(9,2),K(3,3),N(3),Z(8,8),D(8)
    :param input:
    :return:
    """

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


# For now, don't tokenize in advance
def stmt_rem(executor, stmt):
    """
    Does nothing.
    :return:
    """
    return None


def stmt_print(executor, stmt):
    print(stmt.args[1:-1])
    return None

def stmt_for(executor, stmt):
    pass
    #raise Exception("Not implmented")

def stmt_exp(executor, stmt):
    try:
        variable, value = stmt.args.split("=", 1)
    except Exception as e:
        print(e)
    if variable.endswith("$"):
        value = value[1:-1]
    executor._symbols[variable] = value

def stmt_dim(executor, stmt):
    stmts = smart_split(stmt.args.strip(), "(", ")", ",")
    for s in stmts:
        name = s[0]
        if s[1] in "0123456789]":
            name += s[1]
        if s[len(name)] == "$":
            name += "$"
        dimensions = s[len(name):]
        executor.put_symbol(name, dimensions) # Not right, but for now.

def stmt_goto(executor, stmt):
    pass
def stmt_next(executor, stmt):
    pass
def stmt_if(executor, stmt):
    pass
def stmt_gosub(executor, stmt):
    pass
def stmt_input(executor, stmt):
    pass
def stmt_on(executor, stmt):
    pass
def stmt_end(executor, stmt):
    print("Halting")
    executor.halt()


def stmt_def(executor, stmt):
    try:
        variable, value = stmt.args.split("=", 1)
    except Exception as e:
        print(e)
    variable = variable.strip()
    value = value.strip()
    executor._symbols[variable] = value

def stmt_return(executor, stmt):
    pass

class Keywords(Enum):
    DEF = stmt_def, # User defined functions
    DIM = stmt_dim,
    END = stmt_end,
    EXP = stmt_exp,
    FOR = stmt_for,
    GOTO = stmt_goto,
    GOSUB = stmt_gosub,
    IF = stmt_if,
    INPUT = stmt_input,
    NEXT = stmt_next,
    ON = stmt_on, # Computed gotos
    PRINT = stmt_print,
    REM = stmt_rem,
    RETURN= stmt_return,


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


def load_program(program_filename):
    with open(program_filename) as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    program = tokenize(lines)
    return program


class Execution:
    def __init__(self, program):
        self._program = program
        self._current = program[0]
        self._symbols = {}
        self._run = False

    def halt(self):
        self._run = False

    def run_program(self):
        #program = load_program(program_filename)
        self._run = True
        trace = False
        while self._run:
            if trace:
                print(F"{self._current.line}: ")
            # Get the statements on the current line
            stmts = self._current.stmts
            for s in stmts:
                if trace:
                    print("\t", s.keyword, s.args)
                execution_function = s.keyword.value
                # Not sure why execution function is coming back a tuple
                execution_function[0](self, s)
                # TODO Handle goto, loops, and other control transfers
            if self._current.next != -1:
                self._current = self._program[self._current.next]
            else:
                self._run = False

    def get_symbols(self):
        return self._symbols.copy()

    def put_symbol(self, symbol, value):
        self._symbols[symbol] = value

    def get_symbol(self, symbol):
        """
        This function is just for testing.
        :param symbol:
        :return:
        """
        return self._symbols[symbol]

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
        lines.append(current)
    return lines


def print_formatted(program, f = sys.stdout):
    lines = format_program(program)
    for line in lines:
        print(line)


if __name__ == "__main__":
    program = load_program("superstartrek.bas")
    executor = Execution(program)
    executor.run_program()
    import pprint
    pprint.pprint(executor.get_symbols())


