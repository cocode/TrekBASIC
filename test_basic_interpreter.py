from unittest import TestCase
from basic_interpreter import tokenize_line, statement, statements, Keywords, smart_split
from basic_interpreter import load_program, print_formatted


class Test(TestCase):
    def test_token_rem(self):
        line = "10 REM SUPER STARTREK - MAY 16,1978 - REQUIRES 24K MEMORY"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, statements))
        self.assertEqual(10, results.line)
        self.assertEqual(1, len(results.stmts))
        self.assertEqual(Keywords.REM, results.stmts[0].keyword)
        # Note leading space.
        self.assertEqual(" SUPER STARTREK - MAY 16,1978 - REQUIRES 24K MEMORY", results.stmts[0].args)

    def test_token_for(self):
        line = "820 FORI=1TO8"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, statements))
        self.assertEqual(820, results.line)
        self.assertEqual(1, len(results.stmts))
        self.assertEqual(Keywords.FOR, results.stmts[0].keyword)
        self.assertEqual("I=1TO8", results.stmts[0].args)

    def test_token_exp(self):
        multi_exp = "T=INT(RND(1)*20+20)*100:T0=T:T9=25+INT(RND(1)*10):D0=0:E=3000:E0=E"
        line = f"370 {multi_exp}"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, statements))
        self.assertEqual(370, results.line)
        self.assertEqual(6, len(results.stmts))
        expect = multi_exp.split(":")
        self.assertEqual(6, len(expect))
        for i in range(len(expect)):
            self.assertEqual(Keywords.EXP, results.stmts[i].keyword)
            self.assertEqual(expect[i], results.stmts[i].args)

    def test_multiple(self):
        """
        Test multiple, colon separated statements on one line.
        :return:
        """
        line = '1460 PRINT"YOUR MISSION: BEGINS":PRINT"AND ENDS"'
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, statements))
        self.assertEqual(1460, results.line)
        self.assertEqual(2, len(results.stmts))

        result = results.stmts[0]
        self.assertEqual(Keywords.PRINT, result.keyword)
        self.assertEqual('"YOUR MISSION: BEGINS"', result.args)

        result = results.stmts[1]
        self.assertEqual(Keywords.PRINT, result.keyword)
        self.assertEqual('"AND ENDS"', result.args)

    def test_smart_split(self):
        line = 'PRINT"YOUR MISSION: BEGINS":PRINT"AND ENDS"'
        results = smart_split(line)
        self.assertEqual(2, len(results))
        self.assertEqual('PRINT"YOUR MISSION: BEGINS"', results[0])
        self.assertEqual('PRINT"AND ENDS"', results[1])

    def test_load_program(self):
        program = load_program("superstartrek.bas")
        self.assertEqual(425, len(program))
        with open("test_output.txt", 'w') as f:
            print_formatted(program, f)