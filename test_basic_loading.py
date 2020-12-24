from io import StringIO
from unittest import TestCase
import sys

from basic_statements import Keywords
from basic_types import ProgramLine
from basic_loading import tokenize_line, load_program
from basic_utils import format_program


class Test(TestCase):
    def test_todo(self):
        pass # There should be a test for the tokenize() function.
            # especially for IF THEN

    def test_token_rem(self):
        line = "10 REM SUPER STARTREK - MAY 16,1978 - REQUIRES 24K MEMORY"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, ProgramLine))
        self.assertEqual(10, results.line)
        self.assertEqual(1, len(results.stmts))
        self.assertEqual(Keywords.REM, results.stmts[0].keyword)
        # Note leading space.
        self.assertEqual(" SUPER STARTREK - MAY 16,1978 - REQUIRES 24K MEMORY", results.stmts[0].args)

    def test_token_for(self):
        line = "820 FORI=1TO8"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, ProgramLine))
        self.assertEqual(820, results.line)
        self.assertEqual(1, len(results.stmts))
        self.assertEqual(Keywords.FOR, results.stmts[0].keyword)
        p = results.stmts[0]
        self.assertEqual("I", p._index_clause)
        self.assertEqual("1", p._start_clause)
        self.assertEqual("8", p._to_clause)
        self.assertEqual("1", p._step_clause)

    def test_token_exp(self):
        multi_exp = "T=INT(RND(1)*20+20)*100:T0=T:T9=25+INT(RND(1)*10):D0=0:E=3000:E0=E"
        line = f"370 {multi_exp}"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, ProgramLine))
        self.assertEqual(370, results.line)
        self.assertEqual(6, len(results.stmts))
        expect = multi_exp.split(":")
        self.assertEqual(6, len(expect))
        for i in range(len(expect)):
            self.assertEqual(Keywords.LET, results.stmts[i].keyword)
            self.assertEqual(expect[i], results.stmts[i].args)


    def test_tokenize_if(self):
        clause = "IF3<>2THENX=3"
        line = f"370 {clause}"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, ProgramLine))
        self.assertEqual(370, results.line)
        self.assertEqual(2, len(results.stmts))


    def test_multiple(self):
        """
        Test multiple, colon separated statements on one line.
        :return:
        """
        line = '1460 PRINT"YOUR MISSION: BEGINS":PRINT"AND ENDS"'
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, ProgramLine))
        self.assertEqual(1460, results.line)
        self.assertEqual(2, len(results.stmts))

        result = results.stmts[0]
        self.assertEqual(Keywords.PRINT, result.keyword)
        self.assertEqual('"YOUR MISSION: BEGINS"', result.args)

        result = results.stmts[1]
        self.assertEqual(Keywords.PRINT, result.keyword)
        self.assertEqual('"AND ENDS"', result.args)

    def test_multiple_for(self):
        line = "530 NEXTI"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, ProgramLine))
        self.assertEqual(530, results.line)
        self.assertEqual(1, len(results.stmts))

        result = results.stmts[0]
        self.assertEqual(Keywords.NEXT, result.keyword)
        self.assertEqual('I', result.loop_var)

        line = "530 FORI=1TO9:C(I,1)=0:C(I,2)=0:NEXTI"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, ProgramLine))
        self.assertEqual(530, results.line)
        self.assertEqual(4, len(results.stmts))

        result = results.stmts[1]
        self.assertEqual(Keywords.LET, result.keyword)
        self.assertEqual('C(I,1)=0', result.args)

        result = results.stmts[2]
        self.assertEqual(Keywords.LET, result.keyword)
        self.assertEqual('C(I,2)=0', result.args)

        result = results.stmts[3]
        self.assertEqual(Keywords.NEXT, result.keyword)
        self.assertEqual('I', result.loop_var)

    def test_load_program(self):
        program = load_program("simple_test.bas")
        self.assertEqual(5, len(program))
        with open("sample_output.txt", 'w') as f:
            for line in format_program(program):
                print(line, file=f)
            # TODO Compare output to source
