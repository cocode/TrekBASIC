from unittest import TestCase
from parsed_statements import ParsedStatementFor

class TestParsedStatementFor(TestCase):
    def test_parsing(self):
        p = ParsedStatementFor("FOR", " I = 1 TO 10 STEP 2")
        self.assertEqual("I", p._index_clause)
        self.assertEqual("1", p._start_clause)
        self.assertEqual("10", p._to_clause)
        self.assertEqual("2", p._step_clause)

        p = ParsedStatementFor("FOR", "I5=100TOX(3)STEP-Y")
        self.assertEqual("I5", p._index_clause)
        self.assertEqual("100", p._start_clause)
        self.assertEqual("X(3)", p._to_clause)
        self.assertEqual("-Y", p._step_clause)
