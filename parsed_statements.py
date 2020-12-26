"""
This file contains the classes used to represent parsed statements.
"""
from basic_lexer import get_lexer
from basic_types import tokens_to_str, NUMBERS

from basic_types import is_valid_identifier
from basic_types import assert_syntax, BasicSyntaxError
from basic_expressions import Expression
from basic_utils import smart_split


class ParsedStatement:
    """
    Base class for a statement that requires no extra processing.
    """
    def __init__(self, keyword, args):
        """
        Represents a (partially, optianally) pre-processed form of a statement.

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

    def __str__(self):
        """
        This generates syntaxtically valid, nicely formatted versions of the statement.
        :return:
        """
        return F"{self.keyword.name} {self.args}"

class ParsedStatementNoArgs(ParsedStatement):
    """
    Base class for a statement that takes no arguments. END, RETURN, STOP
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        self.keyword = keyword
        assert_syntax(len(args.strip())==0, "Command does not take any arguments.")
        self.args = ""


class ParsedStatementIf(ParsedStatement):
    """
    Class for a IF statement that has been processed.
    """
    # TODO superstartrek3.bas uses an ELSE
    # Notes for ELSE. IF...THEN current works be branching to the next line, if the condition is False.
    # For else, it would branch to after the ELSE clause, if the condition is false, on the same line.
    # superstartrek3.bas only uses the ELSE on the same line as the THEN.
    # We need to parse the clauses after then ELSE, and add them to the line, like we now do with _additional
    # and we need to know the offset of the statements after the else.
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        then = args.find("THEN")
        assert_syntax(then != -1, "No THEN found for IF")
        then_clause = args[then+len("THEN"):]
        self._additional = then_clause.strip()
        lexer = get_lexer()
        left_over = args[:then]
        self._tokens = lexer.lex(left_over)
        super().__init__(keyword, "")

    def get_additional(self):
        return self._additional

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
            input_vars = split_args[0]
        else:
            assert_syntax(len(split_args) == 2, "INPUT statment should only have one ;")
            self._prompt = split_args[0].strip()
            input_vars = split_args[1]
        input_vars = input_vars.split(",")
        input_vars = [v.strip() for v in input_vars]
        [is_valid_identifier(v) for v in input_vars]
        self._input_vars = input_vars

    def __str__(self):
        return F'{self.keyword.name} {self._prompt};{",".join(self._input_vars)}'


class ParsedStatementGo(ParsedStatement):
    """
    Class for a GOTO, GOSUB statement that has been processed.
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        self.destination = args.strip()
        assert_syntax(str.isdigit(self.destination), F"GOTO/GOSUB target is not an int ")

    def __str__(self):
        return F"{self.keyword.name} {self.destination}"


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
    Handles LET statements, whether or not they have an explicit LET
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")

        try:
            variable, value = args.split("=", 1)
        except Exception as e:
            raise BasicSyntaxError(F"Error in expression. No '='.")

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
        self._dimensions = {}

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
            assert_syntax(dimensions[-1] == ')', "Missing (")
            dimensions = dimensions[1:-1]  # Remove parens
            dimensions = dimensions.split(",")
            assert len(dimensions) <= 2 and len(dimensions) > 0
            if len(dimensions) == 1:
                size = int(dimensions[0])
                value = [0] * size
            elif len(dimensions) == 2:
                size_x = int(dimensions[0].replace("(", ''))
                size_y = int(dimensions[1].replace(")", ''))
                value = [[0] * size_y for _ in range(size_x)]  # wrong: [[0] * size_y] * size_x
            else:
                assert_syntax(False, F"Too many dimensions {len(dimensions)}")
            assert_syntax(name not in self._dimensions, "duplicated variable in DIM")
            self._dimensions[name] = value