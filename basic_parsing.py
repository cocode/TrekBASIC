"""
This file contains the classes used to represent parsed statements.
"""
from basic_lexer import get_lexer
from basic_find_str_quotes import find_next_str_not_quoted
from basic_types import tokens_to_str, NUMBERS

from basic_types import is_valid_identifier
from basic_types import assert_syntax, BasicSyntaxError
from basic_expressions import Expression
from basic_utils import smart_split
import copy


class ParsedStatement:
    """
    Base class for a statement that requires no extra processing.

    ParsedStatements are used in renumber, so they have to store enough information to
    completely rebuild themselves. You can't discard information just because it's not
    needed for execution.
    """
    def __init__(self, keyword, args):
        """
        Represents a (partially, optionally) pre-processed form of a statement.

        We should be doing more processing on program load, so as to do less when executing.
        For example, we should tokenize expressions here, so we don't have to do it every
        time we execute the line.
        :param keyword: The keyword for the line, for example: IF
        :param args: Any unparsed arguments. ParsedSatement subclasses may consume this. May be "", may not be None
        """
        assert args is not None
        self.keyword = keyword
        args = args.strip()
        self.args = args

    def get_additional(self):
        return [] # Only used by if statement

    def renumber(self, line_map):
        return copy.copy(self)

    def __str__(self):
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
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        self.keyword = keyword  # TODO Do we need this, it's in the base class?
        assert_syntax(len(args.strip())== 0, "Command does not take any arguments.")
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

    """
    # TODO superstartrek3.bas uses an ELSE
    # Notes for ELSE.
    # IF a=b THEN y=z ELSE y=a
    # If a T
    # IF...THEN current works be branching to the next line, if the condition is False.
    # For else, it would branch to after the ELSE clause, if the condition is false, on the same line.
    # superstartrek3.bas only uses the ELSE on the same line as the THEN.
    # We need to parse the clauses after then ELSE, and add them to the line, like we now do with _additional
    # and we need to know the offset of the statements after the else.
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        # then = args.upper().find("THEN") # TODO watch for quotes
        # assert_syntax(then != -1, "No THEN found for IF")
        then, then_end = find_next_str_not_quoted(args.upper(), "THEN")
        assert_syntax(then is not None, "No THEN found for IF")
        then_clause = args[then+len("THEN"):]
        self._additional = then_clause.strip()
        lexer = get_lexer()
        left_over = args[:then]
        self._tokens = lexer.lex(left_over)

    def get_additional(self):
        return self._additional

    def clear_additional(self):
        self._additional = ""

    def __str__(self):
        clause = tokens_to_str(self._tokens)
        return F"{self.keyword.name} {clause} THEN {self._additional}"

class ParsedStatementFor(ParsedStatement):
    """
    Class for a FOR statement that has been processed.
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        eq = args.find("=")
        to = args.find("TO")
        step = args.find("STEP")
        assert_syntax(eq != -1, "No = found for FOR")
        assert_syntax(to != -1, "No TO found for FOR")
        self._index_clause = args[:eq].strip() # TODO convert to int here.
        self._start_clause = args[eq+1:to].strip()
        end_to = step if step != -1 else None
        self._to_clause = args[to+2:end_to].strip()
        if step == -1:
            self._step_clause = '1'
        else:
            self._step_clause = args[step+4:].strip()

    def __str__(self):
        s = F"{self.keyword.name} {self._index_clause} = {self._start_clause} TO {self._to_clause}"
        if self._step_clause != '1':
            s += F" step {self._step_clause}"
        return s


class ParsedStatementNext(ParsedStatement):
    """
    Class for a NEXT statement that has been processed.
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        self.loop_var = args.strip()

    def __str__(self):
        return F"{self.keyword.name} {self.loop_var}"


class ParsedStatementInput(ParsedStatement):
    """
    Class for an INPUT statement that has been processed.
    TODO In superstartrek3.bas, input takes multiple prompt expressions, separated by semicolons
    """
    def __init__(self, keyword, args):
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
        self._input_vars = input_vars

    def __str__(self):
        if self._prompt:
            return F'{self.keyword.name} {self._prompt};{",".join(self._input_vars)}'
        else:
            return F'{self.keyword.name} {",".join(self._input_vars)}'


class ParsedStatementGo(ParsedStatement):
    """
    Class for a GOTO, GOSUB statement that has been processed.
    """
    def __init__(self, keyword, args):
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
            self._target_lines = on_stmt._target_lines
            self.destination = None  # Not used for computed GOTO/GOSUB
        else:
            # Regular GOTO/GOSUB with single destination
            self._is_computed = False
            self.destination = args
            assert_syntax(str.isdigit(self.destination), F"GOTO/GOSUB target is not an int ")

    def __str__(self):
        if hasattr(self, '_is_computed') and self._is_computed:
            l2 = [str(l) for l in self._target_lines]
            return F"{self.keyword.name} {self._expression} OF {','.join(l2)}"
        else:
            return F"{self.keyword.name} {self.destination}"

    def renumber(self, line_map):
        if hasattr(self, '_is_computed') and self._is_computed:
            # Renumber computed GOTO/GOSUB
            new_targets = [line_map[line] for line in self._target_lines]
            # Create a new computed GOTO/GOSUB
            new_stmt = ParsedStatementGo(self.keyword, "")
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
    def __init__(self, keyword, args):
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
            assert_syntax(str.isdigit(line), F"Invalid line {line} for target of ON GOTO/GOSUB")
            line = int(line)
            lines2.append(line) # Why are these ints?
        self._target_lines = lines2

    def __str__(self):
        l2 = [str(l) for l in self._target_lines]
        return F"{self.keyword.name} {self._expression} {self._op} {','.join(l2)}"


class ParsedStatementLet(ParsedStatement):
    """
    Handles LET statements, whether they have an explicit LET or not.
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        if "=" not in args:
            raise BasicSyntaxError(F"Command not recognized. '{args}'")

        try:
            variable, value = args.split("=", 1)
        except Exception as e:
            raise BasicSyntaxError(F"Error in expression. No '='.")

        variable = variable.strip()

        lexer = get_lexer()
        self._tokens = lexer.lex(value)
        self._expression = Expression()
        self._variable = variable.strip()

    def __str__(self):
        return F"{self.keyword.name} {self._variable}={tokens_to_str(self._tokens)}"


class ParsedStatementDef(ParsedStatement):
    """
    Handles DEF statements
    TODO Could compute constant expressions here, if any. 2*3+X is 6*x
    """
    def __init__(self, keyword, args):
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
        self._tokens = lexer.lex(value)
        self._value = value.strip()

    def __str__(self):
        return F"{self.keyword.name} {self._variable}({self._function_arg})={self._value}"


class ParsedStatementPrint(ParsedStatement):
    """
    Handles PRINT statements
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")

        args = args.strip()
        if args.endswith(";"):
            self._no_cr = True
        else:
            self._no_cr = False
        self._outputs = []
        args = smart_split(args, split_char=";")
        # TODO have a print_arg type, that tells stmt_print whether it is a quoted string or an expression
        # Of course, a quited string should be an expression, so maybe I don't need both branches.
        for i, arg in enumerate(args):
            arg = arg.strip()
            if len(arg) == 0:
                continue
            if arg[0] == '"': # quoted string
                assert_syntax(arg[0] =='"' and arg[-1] == '"', "String not properly quoted for 'PRINT'")
                self._outputs.append(arg)
            else: # Expression
                self._outputs.append(arg) # TODO Parse it here, evaluate in stmt_print
        return

    def __str__(self):
        c = ";" if self._no_cr else ""
        return F'{self.keyword.name} {";".join(self._outputs)}{c}'


class ParsedStatementDim(ParsedStatement):
    """
    Handles DIM statements
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        self._dimensions = []

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

    def __str__(self):
        all = [name+"("+",".join(dims)+")" for name, dims in self._dimensions]
        return F"{self.keyword.name} {','.join(all)}"

class ParsedStatementTrace(ParsedStatement):
    """
    Handles Trace statments - this are not program statements, there evnironmental control options.
    This turns on and off writing line number information to a trace file.
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        args = args.strip()
        valid = ["on", "off"]
        if args not in valid:
            raise BasicSyntaxError(F"Arguments to trace must be one of {valid}, but got {args}")
        self.state = args

    def __str__(self):
        return F"{self.keyword.name} {self.state}"

class ParsedStatementData(ParsedStatement):
    """
    Handles DATA statements - stores values as strings for later type conversion
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        args = args.strip()
        if not args:
            self._values = []
        else:
            # Split by commas, but preserve quoted strings
            values = smart_split(args, split_char=",")
            self._values = [v.strip() for v in values]

    def __str__(self):
        return F"{self.keyword.name} {','.join(self._values)}"


class ParsedStatementRead(ParsedStatement):
    """
    Handles READ statements - stores list of variable names to read into
    """
    def __init__(self, keyword, args):
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
        
        self._variables = variables
        
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

    def __str__(self):
        return F"{self.keyword.name} {','.join(self._variables)}"


class ParsedStatementRestore(ParsedStatement):
    """
    Handles RESTORE statements - optionally takes a line number
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        args = args.strip()
        if not args:
            self._line_number = None
        else:
            # Should be a line number
            if not args.isdigit():
                raise BasicSyntaxError(f"RESTORE requires a line number, got '{args}'")
            self._line_number = int(args)

    def __str__(self):
        if self._line_number is None:
            return self.keyword.name
        else:
            return F"{self.keyword.name} {self._line_number}"
