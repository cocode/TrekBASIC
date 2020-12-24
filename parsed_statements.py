"""
This file contains the classes used to represent parsed statements.
"""
from basic_lexer import Lexer
from basic_types import assert_syntax, BasicSyntaxError
from basic_expressions import Expression


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
        :param args: Any unparsed arguments. ParsedSatement subclasses may consume this.
        """
        self.keyword = keyword
        self.args = args

    def get_additional(self):
        return [] # Only used by if statement


class ParsedStatementNoArgs(ParsedStatement):
    """
    Base class for a statement that takes no arguments. END, RETURN, STOP
    """
    def __init__(self, keyword, args):
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
        then = args.find("THEN")
        assert_syntax(then != -1, "No THEN found for IF")
        then_clause = args[then+len("THEN"):]
        self._additional = then_clause
        lexer = Lexer()
        left_over = args[:then]
        self._tokens = lexer.lex(left_over)
        super().__init__(keyword, None)

    def get_additional(self):
        return self._additional


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
        self._index_clause = args[:eq].strip()
        self._start_clause = args[eq+1:to].strip()
        end_to = step if step != -1 else None
        self._to_clause = args[to+2:end_to].strip()
        if step == -1:
            self._step_clause = '1'
        else:
            self._step_clause = args[step+4:].strip()


class ParsedStatementNext(ParsedStatement):
    """
    Class for a NEXT statement that has been processed.
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        self.loop_var = args.strip()


class ParsedStatementInput(ParsedStatement):
    """
    Class for an INPUT statement that has been processed.
    TODO In superstartrek3.bas, input takes multiple prompt expressions, separated by semicolons
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        delim = args.find(";")
        if delim == -1:
            self._prompt = ""
        else:
            self._prompt = args[:delim].strip()
        input_vars = args[delim+1:].strip()
        input_vars = input_vars.split(",")
        input_vars = [v.strip() for v in input_vars]
        self._input_vars = input_vars


class ParsedStatementGo(ParsedStatement):
    """
    Class for a GOTO, GOSUB statement that has been processed.
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        self.destination = args.strip()
        assert_syntax(str.isdigit(self.destination), F"GOTO/GOSUB target is not an int ")


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
            lines2.append(line)
        self._target_lines = lines2


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

        lexer = Lexer()
        self._tokens = lexer.lex(value)
        self._expression = Expression()
        self._variable = variable.strip()


class ParsedStatementDef(ParsedStatement):
    """
    Handles DEF statements
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
        self._value = value.strip()
        # TODO Should we parse the expression here? Currently, it's parsed when the function is USED.





