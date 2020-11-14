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
