"""
Basic interpreter to run superstartrek.
It's not intended (yet) to run ANY basic program.
"""
from collections import namedtuple
import sys
from enum import Enum

from basic_types import statements, lexer_token, BasicSyntaxError, BasicInternalError, assert_syntax, ste
from parsed_statements import ParsedStatement, ParsedStatementIf
from basic_lexer import lexer_token, Lexer, NUMBERS, LETTERS
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

# TODO can print be more complex? PRINT A$,"ABC",B$. I think it can
def stmt_print(executor, stmt):
    arg = stmt.args.strip()
    args = arg.split(";")
    for i, arg in enumerate(args):
        arg = arg.strip()
        if len(arg) == 0:
            continue
        if arg[0] == '"': # quoted string
            assert_syntax(arg[0] =='"' and arg[-1] == '"', "String not properly quoted for 'PRINT'")
            output = arg[1:-1]
            print(output, end='')
        else: # Variable
            v = executor.get_symbol(arg)
            print(F"{v:g}", end='')
        if i < len(args) - 1:
            print(" ", end='')
    print()
    return None


def stmt_goto(executor, stmt):
    destination = stmt.args.strip()
    assert_syntax(str.isdigit(destination), F"Goto target is not an int ")
    executor.goto(int(destination))
    return None

def stmt_for(executor, stmt):
    pass
    #raise Exception("Not implmented")


def is_valid_identifier(variable:str):
    """
    Checks if the identifier is a valid variable name to assign to.
    Assumes that spaces have already been removed.
    Does not recognize internal functions, or user defined functions.
    :param variable: The variable name to check.
    :return: None. Raises an exception if the name is not valid.
    """
    assert_syntax(len(variable) >= 1, F"Zero length variable name.")
    assert_syntax(len(variable) <= 3, F"Variable {variable} too long.")
    assert_syntax(variable[0] in LETTERS, F"Variable {variable} must start with a letters.")
    if len(variable) == 1:
        return
    if len(variable) == 2 and variable[1] == '$':
        return
    assert_syntax(variable[1] in NUMBERS, "Second char of {variable} must be a number or $.")
    if len(variable) == 2:
        return
    assert_syntax(variable[2] == '$', F"Invalid variable name {variable}")


def assign_variable(executor, variable, value):
    """
    Variable assignment can include assigning array elements.
    :param variable:
    :param value:
    :return:
    """
    variable = variable.replace(" ", "")
    # Need to handle array element assignment.
    i = variable.find("(")
    if i != -1:
        # Array reference
        j = variable.find(")", i+1)
        if j == -1:
            raise BasicSyntaxError(F"Missing ) in in array assignment to {variable}")
        if i+1 == j:
            raise BasicSyntaxError(F"Missing array subscript in assignment to {variable}")

        subscripts = variable[i+1:j].split(",")
        # TODO subscripts can be expressions!
        if len(subscripts) > 2:
            raise BasicSyntaxError('Three+ dimensional arrays are not supported')
        variable = variable[:i]
        is_valid_identifier(variable)
        target = executor.get_symbol(variable) # Array must exist. get_symbol will raise if is does not.
        subscript0 = int(subscripts[0])
        if len(subscripts) == 1:
            target[subscript0] = value
        else:
            subscript1 = int(subscripts[1])
            target[subscript0][subscript1] = value
    else:
        is_valid_identifier(variable)
        executor.put_symbol(variable, value, symbol_type="variable", arg=None)

def stmt_exp(executor, stmt):
    try:
        variable, value = stmt.args.split("=", 1)
    except Exception as e:
        raise BasicSyntaxError(F"Error in expression. No '='.")
    variable = variable.strip()
    lexer = Lexer()
    tokens = lexer.lex(value)
    e = Expression()
    result = e.eval(tokens, symbols=executor._symbols.get_copy())
    assign_variable(executor, variable, result)


def stmt_dim(executor, stmt):
    stmts = smart_split(stmt.args.strip(), "(", ")", ",")
    for s in stmts:
        s = s.strip()
        # TODO a 'get_identifier' function
        name = s[0]
        assert_syntax(len(s) > 1, "Missing dimensions")
        if s[1] in NUMBERS:
            name += s[1]
        if s[len(name)] == "$":
            name += "$"
        dimensions = s[len(name):]
        # TODO This should be part of Executor. Then assert_syntax would know the line number.
        assert_syntax(dimensions[0] == '(',  "Missing (")
        assert_syntax(dimensions[-1] == ')', "Missing (")
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

def stmt_next(executor, stmt):
    pass

def stmt_if(executor, stmt):
    """
    An if statement works by skipping to the next line, if the THEN clause is false, otherwise
    it continues to execute the clauses after the THEN.
    :param executor:
    :param stmt:
    :return:
    """
    lexer = Lexer()
    tokens = lexer.lex(stmt.args)
    e = Expression()
    result = e.eval(tokens, symbols=executor._symbols.get_copy())
    print("IF REsults", result)
    if not result:
        executor.goto_next()



def stmt_gosub(executor, stmt):
    pass
def stmt_input(executor, stmt):
    pass
def stmt_on(executor, stmt):
    pass

def stmt_end(executor, stmt):
    print("Ending program")
    executor._run = False
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
    assert_syntax(len(variable) == 6 and
                  variable.startswith("FN") and
                  variable[3]=='(' and
                  variable[5]==')',
                  "Function definition error")
    arg = variable[4]
    variable = variable[:3]
    value = value.strip()
    executor.put_symbol(variable, value, "function", arg)

def stmt_return(executor, stmt):
    pass

def parse_args(cmd, text):
    """
    Parse the args of a statement that requires no further parsing, like "PRINT"
    :param text:
    :return:
    """
    return ParsedStatement(cmd, text)

def parse_args_if(cmd, text):
    """
    Parse the args of an if statement
    :param text:
    :return:
    """
    p = ParsedStatementIf(cmd, text)
    return p

class KB:
    def __init__(self, exec, parse=parse_args):
        self._parser = parse
        self._exec = exec

    def get_parser(self):
        return self._parser

    def get_exec(self):
        return self._exec


class Keywords(Enum):
    DEF = KB(stmt_def) # User defined functions
    DIM = KB(stmt_dim)
    END = KB(stmt_end)
    FOR = KB(stmt_for)
    GOTO = KB(stmt_goto)
    GOSUB = KB(stmt_gosub)
    IF = KB(stmt_if, parse_args_if)
    INPUT = KB(stmt_input)
    LET = KB(stmt_exp)
    NEXT = KB(stmt_next)
    ON = KB(stmt_on) # Computed gotos
    PRINT = KB(stmt_print)
    REM = KB(stmt_rem)
    RETURN = KB(stmt_return)


class ProgramLine:
    """
    Represents one line of a program. A line may have multiple statements:
        100 PRINT X:IF X>3:THEN Y=7: GOTO 100
    """
    def __init__(self):
        self._statments = []
        self._conditional_statements = []

    def append(self, statement):
        self._statements.append(statement)


def tokenize_statements(commands_text:str):
    list_of_statements = []
    options = [cmd for cmd in Keywords.__members__.values()]
    for command in commands_text:
        for cmd in options:         # Can't just use a dict, because of lines like "100 FORX=1TO10"
            if command.startswith(cmd.name):
                parser_for_keyword = cmd.value.get_parser()
                parsed_statement = parser_for_keyword(cmd, command[len(cmd.name):])
                break
        else:
            # Assignment expression is the default
            cmd = Keywords.LET
            parser_for_keyword = cmd.value.get_parser()
            parsed_statement = parser_for_keyword(cmd, command)

        list_of_statements.append(parsed_statement)
        # This picks up the clauses after then "THEN" in an "IF ... THEN ..."
        additional_text = parsed_statement.get_additional()
        commands_array = smart_split(additional_text)
        additional = tokenize_statements(commands_array)
        list_of_statements.extend(additional)

    return list_of_statements

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

    # Rem commands don't split on colons, other lines do.
    if partial.startswith(Keywords.REM.name):
        commands_text = [partial]
    else:
        commands_text = smart_split(partial)
    list_of_statements = tokenize_statements(commands_text)
    s = statements(number, list_of_statements, -1)
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
    def __init__(self, program, trace=False):
        self._program = program
        self._current = program[0]
        self._symbols = SymbolTable()
        self._run = False
        self._trace = trace
        self._builtin_count = 0
        self._goto = None


    def set_trace(self, value):
        self._trace = value

    def halt(self):
        self._run = False

    def run_program(self):
        #program = load_program(program_filename)
        self.put_symbol("INT", "⌊", "function", arg=lambda x : int(x))
        self._builtin_count += 1
        self.put_symbol("RND", "⌊", "function", arg=lambda x : int(x))
        self._builtin_count += 1

        self._run = True
        self._count_lines = 0
        self._count_stmts = 0
        while self._run:
            self._count_lines += 1
            if self._trace:
                print(F"{self._current.line}: ")
            # Get the statements on the current line
            stmts = self._current.stmts
            for s in stmts:
                self._count_stmts += 1
                if self._trace:
                    print("\t", s.keyword, s.args)
                execution_function = s.keyword.value.get_exec()
                try:
                    execution_function(self, s)
                except BasicSyntaxError as bse:
                    # TODO: This needs a bit more thought. The tests are checking for exceptions,
                    # TODO and don't need the print statement. The user just needs the message printed.
                    print(F"Syntax Error in line {self.get_line().line}: {bse.message}")
                    raise bse
                except Exception as e:
                    raise BasicInternalError(F"Internal error in line {self.get_line()}: {e}")
                if not self._run:
                    break # Don't do the rest of the line
                if self._goto: # If a goto has happened.
                    if self._trace:
                        print(F"\tGOTO from line {self._current.line} TO {self._goto}.")

                    self._current = self._goto
                    self._goto = None
                    # Note: Have to check for a goto within a line! 100 print:print:goto 100:print "shouldn't see this"
                    break # This will skip the "else" which does the normal "step to next line"
            else:
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
        # TODO Maybe check is_valid_variable here? Have to allow user defined functions, and built-ins, though.
        self._symbols.put_symbol(symbol, value, symbol_type, arg)

    def get_line(self):
        return self._current

    def goto(self, line):
        for possible in self._program:
            if possible.line == line:
                self._goto = possible
                return
        raise BasicSyntaxError(F"No line {line} found to GOTO.")

    def goto_next(self, line):
        """
        This is used by "IF ... THEN...", if the condition is false. It moves us to the next line, instead
        of continuing with the THEN clause.
        :param line:
        :return:
        """
        next = self._current.next
        if next is None:
            self._run = False
        self.goto(next)

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
        if stmt.keyword == Keywords.LET:
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
    executor = Executor(program, trace=True)
    executor.run_program()
    import pprint
    pprint.pprint(executor.get_symbols())


