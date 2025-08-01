"""
This file contains the classes used to represent parsed statements.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from trekbasicpy.basic_expressions import Expression
from trekbasicpy.basic_types import NUMBERS, BasicSyntaxError, assert_syntax, is_valid_identifier, tokens_to_str, \
    is_line_number
from trekbasicpy.basic_utils import smart_split
from trekbasicpy.basic_lexer import get_lexer

import copy


class ParsedStatement:
    """
    Base class for a statement that requires no extra processing.

    ParsedStatements are used in renumber, so they have to store enough information to
    completely rebuild themselves. You can't discard information just because it's not
    needed for execution.
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        """
        Represents a (partially, optionally) pre-processed form of a statement.

        We should be doing more processing on program load, so as to do less when executing.
        For example, we should tokenize expressions here, so we don't have to do it every
        time we execute the line.
        :param keyword: The keyword for the line, for example: IF
        :param args: Any unparsed arguments. ParsedStatement subclasses may consume this. May be "", may not be None
        """
        assert args is not None
        self.keyword: 'Keywords' = keyword
        args = args.strip()
        self.args = args

    def renumber(self, line_map: Dict[int, int]) -> 'ParsedStatement':
        return copy.copy(self)

    def format(self) -> 'ParsedStatement':
        return copy.copy(self)

    def __str__(self) -> str:
        """
        This generates syntactically valid, nicely formatted versions of the statement.
        :return:
        """
        if self.args:
            return F"{self.keyword.name} {self.args}"
        else:
            return F"{self.keyword.name}"


class ParsedStatementNoArgs(ParsedStatement):
    """
    Base class for a statement that takes no arguments. END, RETURN, STOP
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        assert_syntax(len(args.strip()) == 0, "Command does not take any arguments.")
        self.args = ""

class ParsedStatementIf(ParsedStatement):
    """
    Class for an "IF" statement that has been processed.
    Cases:
        IF a=b THEN c=d
        IF a=b THEN c=d ELSE d=f
        if A=B THEN c=d IF f=g ELSE d=f         # Else binds to closest
        IF a=b THEN c=d IF q=p ELSE d=f ELSE y=z
        IF a=b THEN c=d:j=x:q=p ELSE d=f:PRINT "ELSE":x=f ELSE y=z

    And negative cases like
        IF a=b ELSE c=d
        IF a=b THEN c=d ELSE d=f ELSE y=z

    Each simple expression above (like "a") can be any expression

    An IF statement runs until it hits the end of a line, or it hits an else statement.

    New version: We don't see the THEN statement here. We just get IF expression
    """
    # IF...THEN currently works be branching to the next line, if the condition is False.
    # For else, it would branch to after the ELSE clause, if the condition is false, on the same line.
    # superstartrek3.bas only uses the ELSE on the same line as the THEN.
    # and we need to know the offset of the statements after the else.
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        lexer = get_lexer()
        left_over = args
        self._tokens: List[Any] = lexer.lex(left_over)

    def __str__(self) -> str:
        clause = tokens_to_str(self._tokens)
        return F"{self.keyword.name} {clause}"

class ParsedStatementFor(ParsedStatement):
    """
    Class for a FOR statement that has been processed.
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        eq = args.find("=")
        to = args.upper().find("TO")
        step = args.upper().find("STEP")
        assert_syntax(eq != -1, "No = found for FOR")
        assert_syntax(to != -1, "No TO found for FOR")
        self._index_clause = args[:eq].strip()  # TODO convert to int here.
        self._start_clause = args[eq+1:to].strip()
        end_to = step if step != -1 else None
        self._to_clause = args[to+2:end_to].strip()
        if step == -1:
            self._step_clause = '1'
        else:
            self._step_clause = args[step+4:].strip()

    def get_args(self) -> str:
        args = F"{self._index_clause} = {self._start_clause} TO {self._to_clause}"
        # TODO Only include step if not 1? Or if no explicity step clause.
        args += " STEP " + self._step_clause
        return args


    def format(self):
        return ParsedStatementFor(self.keyword, self.get_args())

    def __str__(self) -> str:
        s = F"{self.keyword.name} {self.get_args()}"
        if self._step_clause != '1':
            s += F" step {self._step_clause}"
        return s


class ParsedStatementNext(ParsedStatement):
    """
    Class for a NEXT statement that has been processed.
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        self.loop_var = args.strip()

    def __str__(self) -> str:
        return F"{self.keyword.name} {self.loop_var}"


class ParsedStatementInput(ParsedStatement):
    """
    Class for an INPUT statement that has been processed.
    TODO In superstartrek3.bas, input takes multiple prompt expressions, separated by semicolons
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        split_args = smart_split(args, split_char=";")
        if len(split_args) == 1:
            # No prompt
            self._prompt = ""
            input_vars_str = split_args[0]
        else:
            assert_syntax(len(split_args) == 2, "INPUT statment should only have one ;")
            self._prompt = split_args[0].strip()
            input_vars_str = split_args[1]
            
        # Parse variables, handling array elements manually
        input_vars = []
        current_var = ""
        paren_count = 0
        
        for char in input_vars_str + ",":  # Add comma to process last variable
            if char == "," and paren_count == 0:
                if current_var.strip():
                    input_vars.append(current_var.strip())
                current_var = ""
            else:
                current_var += char
                if char == "(":
                    paren_count += 1
                elif char == ")":
                    paren_count -= 1
        
        # Validate each variable (could be simple variable or array element)
        for var in input_vars:
            var_clean = var.replace(" ", "")
            i = var_clean.find("(")
            if i != -1:
                # Array element - validate base variable name only
                base_var = var_clean[:i]
                is_valid_identifier(base_var)
            else:
                # Simple variable
                is_valid_identifier(var)
        self._input_vars: List[str] = input_vars

    def __str__(self) -> str:
        if self._prompt:
            return F'{self.keyword.name} {self._prompt};{",".join(self._input_vars)}'
        else:
            return F'{self.keyword.name} {",".join(self._input_vars)}'


class ParsedStatementGo(ParsedStatement):
    """
    Class for a GOTO, GOSUB statement that has been processed.
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        args = args.strip()
        
        # Check for computed GOTO/GOSUB syntax: "GOTO expr OF line1,line2..." or "GOSUB expr OF line1,line2..."
        of_pos = args.upper().find(" OF ")
        if of_pos != -1:
            # This is a computed GOTO/GOSUB - convert it to ON format
            expression = args[:of_pos].strip()
            lines_part = args[of_pos + 4:].strip()  # Skip " OF "
            
            # Create equivalent ON statement arguments
            on_args = f"{expression} {keyword.name} {lines_part}"
            
            # Parse as ON statement
            on_stmt = ParsedStatementOnGoto(keyword, on_args)
            
            # Copy the parsed data to this object
            self._is_computed = True
            self._expression = on_stmt._expression
            self._op = on_stmt._op
            self._target_lines: List[int] = on_stmt._target_lines
            self.destination: Optional[str] = None  # Not used for computed GOTO/GOSUB
        else:
            # Regular GOTO/GOSUB with single destination
            self._is_computed = False
            self.destination = args
            assert_syntax(is_line_number(self.destination), F"GOTO/GOSUB target is not an int ")

    def __str__(self) -> str:
        if hasattr(self, '_is_computed') and self._is_computed:
            l2 = [str(line) for line in self._target_lines]
            return F"{self.keyword.name} {self._expression} OF {','.join(l2)}"
        else:
            return F"{self.keyword.name} {self.destination}"

    def renumber(self, line_map: Dict[int, int]) -> 'ParsedStatementGo':
        if hasattr(self, '_is_computed') and self._is_computed:
            # Renumber computed GOTO/GOSUB
            new_targets = [line_map[line] for line in self._target_lines]
            # Create new object without calling constructor to avoid parsing empty args
            new_stmt = object.__new__(ParsedStatementGo)
            new_stmt.keyword = self.keyword
            new_stmt.args = ""
            new_stmt._is_computed = True
            new_stmt._expression = self._expression
            new_stmt._op = self._op
            new_stmt._target_lines = new_targets
            new_stmt.destination = None
            return new_stmt
        else:
            # Regular GOTO/GOSUB renumbering
            new_dest = line_map[int(self.destination)]
            return ParsedStatementGo(self.keyword, str(new_dest))


class ParsedStatementOnGoto(ParsedStatement):
    """
    Handles ON X GOTO 100,200 as well as ON X GOSUB 100,200,300
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")

        delim = args.find("GOTO")
        self._op = "GOTO"
        if delim == -1:
            delim = args.find("GOSUB")
            self._op = "GOSUB"

        assert_syntax(delim != -1, F"No GOTO/GOSUB found for ON statement")
        self._expression = args[:delim].strip()
        lines = args[delim+len(self._op):].strip()
        lines = lines.split(",")
        lines2 = []
        for line in lines:
            line = line.strip()
            assert_syntax(is_line_number(line), F"Invalid line {line} for target of ON GOTO/GOSUB")
            line = int(line)
            lines2.append(line)  # Why are these ints?
        self._target_lines: List[int] = lines2

    def __str__(self) -> str:
        l2 = [str(line) for line in self._target_lines]
        return F"{self.keyword.name} {self._expression} {self._op} {','.join(l2)}"

    def renumber(self, line_map: Dict[int, int]) -> 'ParsedStatementOnGoto':
        """Renumber the target lines in ON...GOTO/GOSUB statements"""
        new_targets = [line_map[line] for line in self._target_lines]
        # Create new object without calling constructor to avoid parsing empty args
        new_stmt = object.__new__(ParsedStatementOnGoto)
        new_stmt.keyword = self.keyword
        new_stmt.args = ""
        new_stmt._expression = self._expression
        new_stmt._op = self._op
        new_stmt._target_lines = new_targets
        return new_stmt


class ParsedStatementRem(ParsedStatement):
    """
    Handles REM statements
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, args=args)

    def __str__(self) -> str:
        return F"{self.keyword.name} {self.args}"


class ParsedStatementLet(ParsedStatement):
    """
    Handles LET statements, whether they have an explicit LET or not.
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        if "=" not in args:
            raise BasicSyntaxError(f"Invalid assignment statement '{args}' - missing '=' operator, or unrecognized command")

        try:
            variable, value = args.split("=", 1)
        except Exception as e:
            raise BasicSyntaxError(F"Error in expression. No '='.") from e

        variable = variable.strip()

        lexer = get_lexer()
        self._tokens: List[Any] = lexer.lex(value)
        self._expression: Expression = Expression()
        self._variable = variable.strip()

    def __str__(self) -> str:
        return F"{self.keyword.name} {self._variable}={tokens_to_str(self._tokens)}"


class ParsedStatementDef(ParsedStatement):
    """
    Handles DEF statements
    TODO Could compute constant expressions here, if any. 2*3+X is 6*x
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")

        try:
            variable, value = args.split("=", 1)
        except Exception as e:
            raise BasicSyntaxError(F"Error in expression. No '='.")

        variable = variable.strip()
        assert_syntax(len(variable) == 6 and
                      variable.startswith("FN") and
                      variable[3] == '(' and
                      variable[5] == ')',
                      "Function definition error")
        self._function_arg = variable[4]
        self._variable = variable[:3]
        lexer = get_lexer()
        self._tokens: List[Any] = lexer.lex(value)
        self._value = value.strip()

    def __str__(self) -> str:
        return F"{self.keyword.name} {self._variable}({self._function_arg})={self._value}"


def parse_concatenated_parts(arg: str) -> List[str]:
    """
    Parse an argument that may contain concatenated strings and expressions.
    
    For example: '"YOU ARE IN ROOM "L(1)' becomes:
    ['"YOU ARE IN ROOM "', 'L(1)']
    
    Returns a list of parts, where each part is either:
    - A quoted string (including the quotes)
    - An expression string
    """
    parts = []
    i = 0
    current_part = ""
    
    while i < len(arg):
        if arg[i] == '"':
            # Start of quoted string - find the end
            if current_part.strip():
                # Save any accumulated expression
                parts.append(current_part.strip())
                current_part = ""
            
            # Find closing quote
            string_start = i
            i += 1  # Skip opening quote
            while i < len(arg) and arg[i] != '"':
                i += 1
            
            if i < len(arg):  # Found closing quote
                i += 1  # Include closing quote
                parts.append(arg[string_start:i])
            else:
                raise BasicSyntaxError(f"Unterminated string in: {arg}")
        else:
            # Accumulate expression characters
            current_part += arg[i]
            i += 1
    
    # Add any remaining expression
    if current_part.strip():
        parts.append(current_part.strip())
    
    return parts



class ParsedStatementPrint(ParsedStatement):
    """
    Handles PRINT statements
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")

        args = args.strip()
        if args.endswith(";") or args.endswith(","):
            self._no_cr = True
        else:
            self._no_cr = False
        self._outputs: List[Union[str, List[str]]] = []
        args = self.split_print_arguments(args)
        for i, arg in enumerate(args):
            arg = arg.strip()
            if len(arg) == 0:
                continue
                
            # All arguments are expressions - let the expression evaluator handle them
            self._outputs.append(arg)
        return

    # TODO: This needs to be with other parsing code. We have different dialects, but
    # This is embedding parsing in a different file and implementation
    def split_print_arguments(self, line: str) -> list[str]:
        args = []
        current = ''
        in_quotes = False
        paren_depth = 0

        for i, c in enumerate(line):
            if c == '"':
                in_quotes = not in_quotes
                current += c
            elif c == '(' and not in_quotes:
                paren_depth += 1
                current += c
            elif c == ')' and not in_quotes:
                paren_depth -= 1
                current += c
            elif c in [',', ';'] and not in_quotes and paren_depth == 0:
                args.append(current.strip())
                args.append(c)  # keep the separator as its own entry
                current = ''
            else:
                current += c

        if current.strip():
            args.append(current.strip())

        return args

    def __str__(self) -> str:
        result = [self.keyword.name]  # Start with "PRINT"
        last_was_sep = False

        for output in self._outputs:
            if output in (";", ","):
                result.append(output)
                last_was_sep = True
            elif isinstance(output, list):
                result.append((" " if last_was_sep else " ") + "".join(output))
                last_was_sep = False
            else:
                result.append((" " if last_was_sep else " ") + output)
                last_was_sep = False

        trailing = ";" if self._no_cr else ""
        return "".join(result) + trailing
class ParsedStatementDim(ParsedStatement):
    """
    Handles DIM statements
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        self._dimensions: List[Tuple[str, List[str]]] = []

        stmts = smart_split(args.strip(), enquote="(", dequote=")", split_char=",")
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
            assert_syntax(dimensions[0] == '(', "Missing (")
            assert_syntax(dimensions[-1] == ')', "Missing )")
            dimensions_str = dimensions[1:-1]  # Remove parens
            
            # Use smart_split to handle function calls with commas
            dimension_list = smart_split(dimensions_str, enquote="(", dequote=")", split_char=",")
            dimension_list = [d.strip() for d in dimension_list]
            
            # Store dimensions as expression strings for runtime evaluation
            # They'll be evaluated in stmt_dim when the symbol table is available
            self._dimensions.append((name, dimension_list))

    def __str__(self) -> str:
        all_names = [name+"("+",".join(dims)+")" for name, dims in self._dimensions]
        return F"{self.keyword.name} {','.join(all_names)}"

class ParsedStatementTrace(ParsedStatement):
    """
    Handles Trace statments - this are not program statements, there evnironmental control options.
    This turns on and off writing line number information to a trace file.
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        args = args.strip()
        valid = ["on", "off"]
        if args not in valid:
            raise BasicSyntaxError(F"Arguments to trace must be one of {valid}, but got {args}")
        self.state = args

    def __str__(self) -> str:
        return F"{self.keyword.name} {self.state}"

class ParsedStatementData(ParsedStatement):
    """
    Handles DATA statements - stores values as strings for later type conversion
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        args = args.strip()
        if not args:
            self._values = []
        else:
            # Split by commas, but preserve quoted strings
            values = smart_split(args, split_char=",")
            self._values = [v.strip() for v in values]

    def __str__(self) -> str:
        return F"{self.keyword.name} {','.join(self._values)}"


class ParsedStatementRead(ParsedStatement):
    """
    Handles READ statements - stores list of variable names to read into
    """
    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        args = args.strip()
        if not args:
            raise BasicSyntaxError("READ statement requires variable names")
        
        # Parse variables, handling array elements manually
        variables = []
        current_var = ""
        paren_count = 0
        
        for char in args + ",":  # Add comma to process last variable
            if char == "," and paren_count == 0:
                if current_var.strip():
                    variables.append(current_var.strip())
                current_var = ""
            else:
                current_var += char
                if char == "(":
                    paren_count += 1
                elif char == ")":
                    paren_count -= 1
        
        self._variables: List[str] = variables
        
        # Validate variable names (including array elements)
        for var in self._variables:
            var_clean = var.replace(" ", "")
            i = var_clean.find("(")
            if i != -1:
                # Array element - validate base variable name only
                base_var = var_clean[:i]
                is_valid_identifier(base_var)
            else:
                # Simple variable
                is_valid_identifier(var)

    def __str__(self) -> str:
        return F"{self.keyword.name} {','.join(self._variables)}"


class ParsedStatementRestore(ParsedStatement):
    """
    Handles RESTORE statements - optionally takes a line number
    """

    def __init__(self, keyword: 'Keywords', args: str) -> None:
        super().__init__(keyword, "")
        args = args.strip()
        if not args:
            self._line_number: Optional[int] = None
        else:
            # Should be a line number
            if not args.isdigit():
                raise BasicSyntaxError(f"RESTORE requires a line number, got '{args}'")
            self._line_number = int(args)

    def __str__(self) -> str:
        if self._line_number is None:
            return self.keyword.name
        else:
            return F"{self.keyword.name} {self._line_number}"

    def renumber(self, line_map: Dict[int, int]) -> 'ParsedStatementRestore':
        """Renumber the line number in RESTORE statements"""
        if self._line_number is None:
            # No line number to renumber
            return self
        else:
            new_line = line_map[self._line_number]
            new_stmt = ParsedStatementRestore(self.keyword, "")
            new_stmt._line_number = new_line
            return new_stmt

class ParsedStatementElse(ParsedStatement):
    """
    Handles THEN statements - No Args, No Op.
    TODO Maybe merge with THEN, they are identical
    """

    def __init__(self, keyword: 'Keywords', _: str) -> None:
        super().__init__(keyword, "")

    def __str__(self) -> str:
        return self.keyword.name

class ParsedStatementThen(ParsedStatement):
    """
    Handles ELSE statements - No Args, No Op.
    """

    def __init__(self, keyword: 'Keywords', _: str) -> None:
        super().__init__(keyword, "")

    def __str__(self) -> str:
        return self.keyword.name
