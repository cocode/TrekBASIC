from unittest import TestCase

from basic_types import BasicSyntaxError
from parsed_statements import ParsedStatementFor, ParsedStatementOnGoto, ParsedStatementInput, ParsedStatementNext, \
    ParsedStatementGo, ParsedStatementNoArgs


class Test(TestCase):

    def test_parsing_for(self):
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

    def test_parsing_next(self):
        p = ParsedStatementNext("NEXT", " J")
        self.assertEqual("J", p.loop_var)

    def test_parsing_go(self):
        p = ParsedStatementGo("GOTO", " 100")
        self.assertEqual("100", p.destination)
        p = ParsedStatementGo("GOSUB", " 2137")
        self.assertEqual("2137", p.destination)
        with self.assertRaises(BasicSyntaxError):
            p = ParsedStatementGo("GOTO", " 100A")

    def test_parsing_on_goto(self):
        p = ParsedStatementOnGoto("ON", "IGOTO100,200,300")
        self.assertEqual("ON", p.keyword)
        self.assertEqual("I", p._expression)
        self.assertEqual("GOTO", p._op)
        self.assertEqual([100, 200, 300], p._target_lines)

        p = ParsedStatementOnGoto("ON", " I5*10+1GOTO 100, 200, 300 ")
        self.assertEqual("ON", p.keyword)
        self.assertEqual("I5*10+1", p._expression)
        self.assertEqual("GOTO", p._op)
        self.assertEqual([100, 200, 300], p._target_lines)

    def test_parsing_input(self):
        p = ParsedStatementInput("INPUT", '"PROMPT IS HERE";A')
        self.assertEqual("INPUT", p.keyword)
        # The prompt is an expression. That's why the nested quotes.
        self.assertEqual('"PROMPT IS HERE"', p._prompt)
        self.assertEqual(["A"], p._input_vars)

        p = ParsedStatementInput("INPUT", '"PROMPT IS HERE";A,B')
        self.assertEqual("INPUT", p.keyword)
        self.assertEqual('"PROMPT IS HERE"', p._prompt)
        self.assertEqual(["A", "B"], p._input_vars)

        p = ParsedStatementInput("INPUT", 'A$;A,B')
        self.assertEqual("INPUT", p.keyword)
        self.assertEqual('A$', p._prompt)
        self.assertEqual(["A", "B"], p._input_vars)


    def test_parsing_end(self):
        p = ParsedStatementNoArgs("END", "")
        self.assertEqual("END", p.keyword)
        self.assertEqual("", p.args)

        with self.assertRaises(BasicSyntaxError):
            p = ParsedStatementNoArgs("END", "SHOULD NOT BE HERE")
