"""
Basic interpreter to run superstartrek.
It's not intended (yet) to run ANY basic program.
"""
from collections import namedtuple
import sys
from enum import Enum, auto

from basic_types import statement, statements, lexer_token, BasicSyntaxError, assert_syntax, ste
from basic_lexer import lexer_token, Lexer, NUMBERS
from basic_expressions import Expression
from basic_symbols import SymbolTable



def smart_split(line:str, enquote:str = '"', dequote:str = '"', split_char:str = ":") -> list[str]:
    """
    Colons split a line up into separate statements. But not if the colon is within quotes.
    Adding comma split, for DIM G(8,8),C(9,2),K(3,3),N(3),Z(8,8),D(8)
    :param line:
    :param enquote: The open quote character.
    :param dequote: The close quote character.
    :param split_char: The character to split on, if not in quotes.
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
        raise BasicSyntaxError(F"Error detected in line {executor.get_line()}. Probably something not implemented.")
    variable = variable.strip()
    lexer = Lexer()
    tokens = lexer.lex(value)
    e = Expression()
    result = e.eval(tokens, symbols=executor._symbols.get_copy())
    executor.put_symbol(variable, result, symbol_type="variable", arg=None)


def stmt_dim(executor, stmt):
    stmts = smart_split(stmt.args.strip(), "(", ")", ",")
    for s in stmts:
        s = s.strip()
        # TODO a 'get_identifier' function
        name = s[0]
        assert_syntax(len(s) > 1, executor.get_line(), "Missing dimensions")
        if s[1] in NUMBERS:
            name += s[1]
        if s[len(name)] == "$":
            name += "$"
        dimensions = s[len(name):]
        # TODO This should be part of Executor. Then assert_syntax would know the line number.
        assert_syntax(dimensions[0] == '(', executor.get_line(), "Missing (")
        assert_syntax(dimensions[-1] == ')', executor.get_line(), "Missing (")
        dimensions = dimensions[1:-1] # Remove parens
        dimensions = dimensions.split(",")
        assert len(dimensions) <= 2 and len(dimensions) > 0
        if len(dimensions) == 1:
            size = int(dimensions[0])
            value = [0] * size
        if len(dimensions) == 2:
            size_x = int(dimensions[0].replace("(",''))
            size_y = int(dimensions[1].replace(")",''))
            value = [[0] * size_y] * size_x
        executor.put_symbol(name, value, "array", arg=None) # Not right, but for now.

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
    """
    Define a user-defined function.

    470 DEF FND(D)=SQR((K(I,1)-S1)^2+(K(I,2)-S2)^2)

    :param executor:
    :param stmt:
    :return:
    """
    try:
        variable, value = stmt.args.split("=", 1)
    except Exception as e:
        print(e)
    variable = variable.strip()
    assert_syntax(len(variable) == 6 and variable.startswith("FN") and variable[3]=='(' and variable[5]==')',
                  executor.get_line(), "Function definition error")
    arg = variable[4]
    variable = variable[:3]
    value = value.strip()
    executor.put_symbol(variable, value, "function", arg)


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
    RETURN = stmt_return,


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


class Executor:
    def __init__(self, program):
        self._program = program
        self._current = program[0]
        self._symbols = SymbolTable()
        self._run = False
        self._trace = False
        self._builtin_count = 0

    def set_trace(self, value):
        self._trace = value

    def halt(self):
        self._run = False

    def run_program(self):
        #program = load_program(program_filename)
        self.put_symbol("INT", "⌊", "function", arg=lambda x : int(x))
        self._builtin_count += 1

        self._run = True
        while self._run:
            if self._trace:
                print(F"{self._current.line}: ")
            # Get the statements on the current line
            stmts = self._current.stmts
            for s in stmts:
                if self._trace:
                    print("\t", s.keyword, s.args)
                execution_function = s.keyword.value
                # Not sure why execution function is coming back a tuple
                execution_function[0](self, s)
                # TODO Handle goto, loops, and other control transfers
            if self._current.next != -1:
                self._current = self._program[self._current.next]
            else:
                self._run = False

    def get_symbol_count(self):
        """
        Get number of defined symbols. Used for testing.
        :return:
        """
        return len(self._symbols)

    def put_symbol(self, symbol, value, symbol_type, arg):
        self._symbols.put_symbol(symbol, value, symbol_type, arg)

    def get_line(self):
        return self._current

    def get_symbol(self, symbol):
        """
        :param symbol:
        :return:
        """
        return self._symbols.get_symbol(symbol)

    def get_symbol_type(self, symbol):
        """
        :param symbol:
        :return:
        """
        return self._symbols.get_symbol_type(symbol)


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
    executor = Executor(program)
    executor.run_program()
    import pprint
    pprint.pprint(executor.get_symbols())


