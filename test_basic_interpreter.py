from unittest import TestCase
from basic_interpreter import tokenize_line, statement, statements, Keywords, smart_split
from basic_interpreter import load_program, format_program, tokenize, Executor, BasicSyntaxError
from basic_lexer import Lexer
from basic_expressions import Expression


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

    def test_multiple_for(self):
        line = "530 NEXTI"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, statements))
        self.assertEqual(530, results.line)
        self.assertEqual(1, len(results.stmts))

        result = results.stmts[0]
        self.assertEqual(Keywords.NEXT, result.keyword)
        self.assertEqual('I', result.args)

        line = "530 FORI=1TO9:C(I,1)=0:C(I,2)=0:NEXTI"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, statements))
        self.assertEqual(530, results.line)
        self.assertEqual(4, len(results.stmts))

        result = results.stmts[0]
        self.assertEqual(Keywords.FOR, result.keyword)
        self.assertEqual('I=1TO9', result.args)

        result = results.stmts[1]
        self.assertEqual(Keywords.EXP, result.keyword)
        self.assertEqual('C(I,1)=0', result.args)

        result = results.stmts[2]
        self.assertEqual(Keywords.EXP, result.keyword)
        self.assertEqual('C(I,2)=0', result.args)

        result = results.stmts[3]
        self.assertEqual(Keywords.NEXT, result.keyword)
        self.assertEqual('I', result.args)


    def test_smart_split(self):
        line = 'PRINT"YOUR MISSION: BEGINS":PRINT"AND ENDS"'
        results = smart_split(line)
        self.assertEqual(2, len(results))
        self.assertEqual('PRINT"YOUR MISSION: BEGINS"', results[0])
        self.assertEqual('PRINT"AND ENDS"', results[1])

        line = "G(8,8),C(9,2),K(3,3),N(3),Z(8,8),D(8)"
        results = smart_split(line, "(", ")", ",")
        self.assertEqual(6, len(results))
        self.assertEqual('G(8,8)', results[0])
        self.assertEqual('C(9,2)', results[1])

    def test_load_program(self):
        program = load_program("superstartrek.bas")
        self.assertEqual(425, len(program))
        with open("sample_output.txt", 'w') as f:
            for line in format_program(program):
                print(line, file=f)
            # TODO Compare output to source

    def test_assignment(self):
        program = tokenize(['100 Z$="Fred"'])
        self.assertEqual(1, len(program))
        executor = Executor(program)
        executor.run_program()
        symbols = executor.get_symbols()
        self.assertEqual(1, len(symbols))
        self.assertEqual('Fred', executor.get_symbol("Z$"))

    def test_dim(self):
        program = tokenize(['100 DIM A(8), C(1,8)'])
        self.assertEqual(1, len(program))
        executor = Executor(program)
        executor.run_program()
        symbols = executor.get_symbols()
        self.assertEqual(2, len(symbols))
        A = executor.get_symbol("A")
        C = executor.get_symbol("C")
        self.assertEqual(8, len(A))
        self.assertEqual(1, len(C))
        self.assertEqual(8, len(C[0]))

    def test_expressions(self):
        listing = [
            '100 A =2+1',
            '110 B=4',
            '120 C = A + B',
            '130 D$="ABC"',
            '140 E$=D$+"DEF"',
        ]
        program = tokenize(listing)
        self.assertEqual(len(listing), len(program))
        executor = Executor(program)
        executor.run_program()
        symbols = executor.get_symbols()
        self.assertEqual(5, len(symbols))
        A = executor.get_symbol("A")
        B = executor.get_symbol("B")
        C = executor.get_symbol("C")
        D = executor.get_symbol("D$")
        E = executor.get_symbol("E$")
        self.assertEqual(A, 3)
        self.assertEqual(B, 4)
        self.assertEqual(C, 7)
        self.assertEqual(D, "ABC")
        self.assertEqual(E, "ABCDEF")

    def test_suite_dim(self):
        """
        Tests with "suite" in the name test for errors.
        :return:
        """
        program = tokenize(['100 DIM A(8'])
        self.assertEqual(1, len(program))
        executor = Executor(program)
        self.assertRaises(BasicSyntaxError, executor.run_program)

        # Assert they gave it a dim May not be right, som edialoects of basic assume 10
        program = tokenize(['100 DIM C'])
        self.assertEqual(1, len(program))
        executor = Executor(program)
        self.assertRaises(BasicSyntaxError, executor.run_program)

