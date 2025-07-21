"""
Lexical analysis for the basic interpreter.
"""

from collections import namedtuple
from enum import Enum, auto
from typing import Optional

# Used internally to tokenize unary minus. This simplifies parsing.
UNARY_MINUS = "—"  # That's an m-dash.
ARRAY_ACCESS = "@"

lexer_token = namedtuple("Token", "token type")

# Represents one line in a basic program, which may be composed of multiple statements
# line: The line of the statement, "100" in "100 PRINT:PRINT:END"
# stmts: A list of statements
# source: The original line as a str
ProgramLineBase = namedtuple("ProgramLine", "line stmts source")

class ProgramLine(ProgramLineBase):
    """
    Subclass of ProgramLine that:
      - compares equality based on (line, stmts), ignoring `source`
      - provides a more compact string representation
    """
    def __eq__(self, other):
        if not isinstance(other, ProgramLine):
            return NotImplemented
        # compare only the fields you care about; here we ignore `source`
        if self.line != other.line:
            print("Line mismatch")
        if self.stmts != other.stmts:
            print("Stmts mismatch")
            for s in range(0, len(self.stmts)):
                print(F"{self.stmts[s]} {other.stmts[s]} {self.stmts[s] == other.stmts[s]}")
        return (self.line, self.stmts) == (other.line, other.stmts)

    def __str__(self):
        stmts_str = ", ".join(str(stmt) for stmt in self.stmts)
        return (
            f"ProgramLine(line={self.line}, stmts=[{stmts_str}], "
            f"source={self.source!r})"
        )

    def __repr__(self):
        # optional: keep repr in sync with str
        return str(self)


# Symbol table entry
# Value - Value of the variable
# Type - SymbolType
# Arg - only used for SymbolType.FUNCTION. The X in DEF FNA(X)=X*X
ste = namedtuple("Symbol", "value type arg")


# Target of a control transfer. Used by GOTO, GOSUB, NEXT, etc.
# index: The index into the Program._lines list
# offset: The index into the ProgramLine.stmts list.
class ControlLocation:
    def __init__(self, index, offset):
        self.index = index
        self.offset = offset

    def __str__(self):
        return f"ControlLocation(index={self.index}, offset={self.offset})"

    def __repr__(self):
        return str(self)


class BasicError(Exception):
    def __init__(self, message, line_number=None):
        super().__init__(message)
        self.message = message

class BasicSyntaxError(BasicError):
    def __init__(self, message, line_number=None):
        super().__init__(message, line_number)
        self.line_number = line_number

class BasicRuntimeError(BasicError):
    def __init__(self, message, line_number=None):
        super().__init__(message, line_number)
        self.line_number = line_number

class UndefinedSymbol(BasicRuntimeError):
    def __init__(self, message, line_number=None, statement_index=None):
        super(UndefinedSymbol, self).__init__(message, line_number)
        self.message = message
        self.line_number = line_number
        self.statement_index = statement_index


class BasicInternalError(Exception):
    def __init__(self, message,):
        super(BasicInternalError, self).__init__(message)


def assert_syntax(value, message):
    if not value:
        raise BasicSyntaxError(F"SyntaxError: {message}")


def assert_internal(value, message):
    if not value:
        raise BasicInternalError(F"InternalError: {message}")


# We had been using a lexical token for the operators, but function calls need more data.
# This what we will push on the op stack, and also pass to the eval function.
# arg, value, and exec are only required for user defined functions.
OP_TOKEN = namedtuple("OPERATION", "token type arg value symbols")


class SymbolType(Enum):
    VARIABLE = auto()
    FUNCTION = auto()
    ARRAY = auto()

# Records the ending status of the program.
class RunStatus(Enum):
    RUN = auto()                  # Running normally
    END_CMD = auto()              # Hit and END statement. Returns status 0 (success)
    END_STOP = auto()             # Hit a STOP statement. Returns status 1 (failed)
    END_OF_PROGRAM = auto()       # Fell of the end of the program. Returns status 0 (success)
    END_ERROR_SYNTAX = auto()
    END_ERROR_INTERNAL = auto()
    END_ERROR_RUNTIME = auto()
    BREAK_CODE = auto()
    BREAK_DATA = auto()
    BREAK_STEP = auto()


NUMBERS = "0123456789]"   # TODO ] is a number? If this value is correct, rename this variable.
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def is_valid_identifier(variable: str) -> None:
    """
    Checks if the identifier is a valid variable name to assign to.
    Assumes that spaces have already been removed.
    Does not recognize internal functions or user defined functions.
    :param variable: The variable name to check.
    :return: None. Raises an exception if the name is not valid.
    """
    assert_syntax(len(variable) >= 1, F"Zero length variable name.")
    assert_syntax(len(variable) <= 3, F"Variable {variable} too long.")
    assert_syntax(variable[0].upper() in LETTERS, F"Variable {variable} must start with a letter.")
    if len(variable) == 1:
        return
    if len(variable) == 2 and variable[1] == '$':
        return
    assert_syntax(variable[1] in NUMBERS, F"Second char of '{variable}' must be a number or $.")
    if len(variable) == 2:
        return
    assert_syntax(variable[2] == '$', F"Invalid variable name {variable}")

def tokens_to_str(tokens: list[lexer_token]):
    s = ""
    for token in tokens:
        if token.type == "num" and int(token.token) == token.token:
            s += str(int(token.token))
        elif token.type == "str":
            s += '"' + token.token + '"'
        else:
            s += str(token.token)
    return s


class Program:
    """
    Encapsulates a BASIC program as a collection of ProgramLine objects.
    Provides methods for navigation, line lookup, and program modification
    while hiding the internal list implementation details.
    """
    
    def __init__(self, program_lines: list[ProgramLine]):
        """
        Initialize with a list of ProgramLine objects.
        Lines should be in ascending line number order.
        """
        # Store the lines
        self._lines = list(program_lines)  # Make a copy
        
        # Build line number to index mapping for fast lookup
        self._line_to_index = {}
        for i, line in enumerate(self._lines):
            self._line_to_index[line.line] = i

    def get_len(self):
        return len(self._lines)

    def get_line(self, index: int) -> ProgramLine:
        """Get line by index in the program"""
        return self._lines[index]
    
    def get_next_index(self, current_index: int) -> Optional[int]:
        """Get the index of the next line, or None if at the end of the program"""
        next_index = current_index + 1
        return next_index if next_index < len(self._lines) else None
    
    def get_next_statement_location(self, current_index: int, current_offset: int):
        """
        Get the location of the next statement in the program.
        
        Args:
            current_index: Current line index in the program
            current_offset: Current statement offset within the line
            
        Returns:
            ControlLocation for the next statement, or None if at the end of program
        """
        next_offset = current_offset + 1
        current_line = self.get_line(current_index)
        
        if next_offset < len(current_line.stmts):
            # More statements on current line
            return ControlLocation(current_index, next_offset)
        else:
            # Move to the first statement of the next line
            next_index = self.get_next_index(current_index)
            if next_index is None:
                return None  # End of program
            return ControlLocation(next_index, 0)
    
    def find_line_index(self, line_number: int) -> int:
        """Find the index for a given line number"""
        if line_number not in self._line_to_index:
            print(f"Line {line_number} not found")
        return self._line_to_index[line_number]

    def get_lines_range(self, start_index: int = 0, count: Optional[int] = None) -> list[str]:
        """Get program lines as strings for display, starting from index"""
        if count is None:
            count = len(self._lines) - start_index

        end_index = min(start_index + count, len(self._lines))
        lines = []

        for i in range(start_index, end_index):
            lines.append(self._lines[i].source)

        return lines

    def get_lines_range2(self, start_index: int, end_index: int) -> list[str]:
        lines = []

        for i in range(start_index, end_index):   # Basic is inclusive of endpoints
            lines.append(self._lines[i].source)

        return lines

    def insert_or_replace_line(self, new_line: ProgramLine) -> bool:
        """
        Insert a new line or replace an existing line.
        Returns True if line was replaced, False if inserted.
        """
        if new_line.line in self._line_to_index:
            # Replace existing line
            index = self._line_to_index[new_line.line]
            self._lines[index] = new_line
            return True
        else:
            # Insert new line in correct position
            insertion_index = 0
            for i, existing_line in enumerate(self._lines):
                if existing_line.line > new_line.line:
                    insertion_index = i
                    break
                insertion_index = i + 1
            
            self._lines.insert(insertion_index, new_line)
            self._rebuild_line_index()
            return False
    
    def delete_line(self, line_number: int) -> bool:
        """
        Delete a line by line number.
        Returns True if line was found and deleted, False otherwise.
        """
        if line_number not in self._line_to_index:
            return False
        
        index = self._line_to_index[line_number]
        del self._lines[index]
        self._rebuild_line_index()
        return True
    
    def _rebuild_line_index(self):
        """Rebuild the line number to index mapping"""
        self._line_to_index = {}
        for i, line in enumerate(self._lines):
            self._line_to_index[line.line] = i
    
    def __len__(self):
        """Return number of lines in program"""
        return len(self._lines)
    
    def __iter__(self):
        """Allow iteration over program lines"""
        return iter(self._lines)
    
    def __getitem__(self, index):
        """Allow indexing into program lines"""
        return self._lines[index]

