"""
This file contains the classes used to represent parsed statements.
"""
from basic_types import assert_syntax


class ParsedStatement:
    """
    Base class for a statement that requires no extra processing.
    """
    def __init__(self, keyword, args):
        self.keyword = keyword
        self.args = args

    def get_additional(self):
        return [] # Only used by if statement


class ParsedStatementIf(ParsedStatement):
    """
    Base class for a statement that has been processed.
    """
    def __init__(self, keyword, args):
        then = args.find("THEN")
        assert_syntax(then != -1, "No THEN found for IF")
        then_clause = args[then+len("THEN"):]
        self._additional = then_clause
        super().__init__(keyword, args[:then])
        # TODO I would like to lex to token steam, and maybe build expression tree here, but don't want circular dependencies

    def get_additional(self):
        return self._additional


class ParsedStatementFor(ParsedStatement):
    """
    Base class for a statement that has been processed.
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


class ParsedStatementInput(ParsedStatement):
    """
    Base class for a statement that has been processed.
    """
    def __init__(self, keyword, args):
        super().__init__(keyword, "")
        delim = args.find(";")
        assert_syntax(delim != -1, "No ; found for INPUT statement")
        self._prompt = args[:delim].strip()
        self._input_var = args[delim+1:].strip()


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


