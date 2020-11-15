from io import StringIO
from unittest import TestCase
import sys

from basic_interpreter import tokenize_line, statements, Keywords, smart_split
from basic_interpreter import load_program, format_program, tokenize, Executor, BasicSyntaxError, is_valid_identifier


class Test(TestCase):
    def assert_value(self, executor, symbol, expected_value):
        value = executor.get_symbol(symbol)
        self.assertEqual(expected_value, value)

    def assert_values(self, executor, expected_values):
        """
        Verifies the symbol table contains the values passed in.
        Does NOT check for extra values.
        :param executor:
        :param expected_values:
        :return: None. Raises an exception, if needed.
        """
        for item in expected_values.items():
            self.assert_value(executor, item[0], item[1])


    def runit(self, listing, trace=False):
        program = tokenize(listing)
        self.assertEqual(len(listing), len(program))
        executor = Executor(program, trace=trace)
        executor.run_program()
        return executor

    def runit_capture(self, listing):
        old = sys.stdout
        output = StringIO()
        sys.stdout = output
        try:
            executor = self.runit(listing)
        finally:
            sys.stdout = old
        program_output = output.getvalue()
        return executor, program_output

    def runit_se(self, listing):
        """
        Run, and verify that the program raises a BasicSyntaxError
        :param listing:
        :return:
        """
        with self.assertRaises(BasicSyntaxError):
            executor = self.runit(listing)

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
            self.assertEqual(Keywords.LET, results.stmts[i].keyword)
            self.assertEqual(expect[i], results.stmts[i].args)

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
            self.assertEqual(Keywords.LET, results.stmts[i].keyword)
            self.assertEqual(expect[i], results.stmts[i].args)

    def test_tokenize_if(self):
        clause = "IF3<>2THENX=3"
        line = f"370 {clause}"
        results = tokenize_line(line)
        self.assertTrue(isinstance(results, statements))
        self.assertEqual(370, results.line)
        self.assertEqual(2, len(results.stmts))


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
        self.assertEqual(Keywords.LET, result.keyword)
        self.assertEqual('C(I,1)=0', result.args)

        result = results.stmts[2]
        self.assertEqual(Keywords.LET, result.keyword)
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
        program = load_program("simple_test.bas")
        self.assertEqual(2, len(program))
        with open("sample_output.txt", 'w') as f:
            for line in format_program(program):
                print(line, file=f)
            # TODO Compare output to source

    def test_assignment(self):
        executor = self.runit(['100 Z$="Fred"'])
        self.assertEqual(1, executor.get_symbol_count()-executor._builtin_count)
        self.assertEqual('Fred', executor.get_symbol("Z$"))

    def test_assignment2(self):
        program = tokenize(['100 TOOLONGVARNAME="Fred"'])
        self.assertEqual(1, len(program))
        executor = Executor(program)
        with self.assertRaises(BasicSyntaxError):
            executor.run_program()

    def test_dim(self):
        executor = self.runit(['100 DIM A(8), C(1,8)'])
        self.assertEqual(2, executor.get_symbol_count()-executor._builtin_count)
        A = executor.get_symbol("A")
        C = executor.get_symbol("C")
        self.assertEqual(8, len(A))
        self.assertEqual(1, len(C))
        self.assertEqual(8, len(C[0]))

    def test_def(self):
        executor = self.runit(['100 DEF FNA(X)=X^2+1'])
        self.assertEqual(1, executor.get_symbol_count()-executor._builtin_count)
        A = executor.get_symbol("FNA")
        AT = executor.get_symbol_type("FNA")
        self.assertEqual("X^2+1", A)
        self.assertEqual("function", AT)

    def test_def2(self):
        listing = [
            '100 DEF FNA(X)=X^2+1',
            '110 Y=FNA(5)',
            '120 Z=FNA(7*7)',
        ]
        executor= self.runit(listing)
        self.assertEqual(3, executor.get_symbol_count()-executor._builtin_count)
        Y = executor.get_symbol("Y")
        self.assertEqual(26, Y)
        Z = executor.get_symbol("Z")
        self.assertEqual(2402, Z)

    def test_def3(self):
        listing = [
            '90 A=2+1',
            '100 DEF FNA(X)=X^A+1',
            '110 Y=FNA(5)',
            '120 Z=FNA(A*A)',
        ]
        executor= self.runit(listing)
        self.assertEqual(4, executor.get_symbol_count()-executor._builtin_count)
        Y = executor.get_symbol("Y")
        Z = executor.get_symbol("Z")
        self.assertEqual(126, Y)
        self.assertEqual(730, Z)

    def test_def4(self):
        listing = [
            '100 DEF FNA(X)=X^2',
            '110 DEF FNB(X)=2*X+3',
            '120 DEF FNC(X)=FNA(3*X)+FNB(X+1)',
            '130 Z=FNC(3)'
        ]
        executor= self.runit(listing)
        self.assertEqual(4, executor.get_symbol_count()-executor._builtin_count)
        Z = executor.get_symbol("Z")
        self.assertEqual(92, Z)

    def test_def5(self):
        listing = [
            '100 DEF FNA(X)=X^2', # 16, 36
            '110 DEF FNB(X)=2*FNA(X)+3', # 35, 75
            '120 X=FNB(4)',
            '130 Y=FNB(6)', # 110
            '140 Z=X+Y'
        ]
        executor= self.runit(listing)
        self.assertEqual(5, executor.get_symbol_count()-executor._builtin_count)
        Z = executor.get_symbol("Z")
        self.assertEqual(110, Z)

    def test_def6(self):
        listing = [
            '100 DEF FNA(X)=X^2', # 16, 36
            '110 DEF FNB(X)=2*FNA(X)+3', # 35, 75
            '120 DEF FNC(X)=FNB(X+1)+FNB(X*2)', # 110
            '130 Z=FNC(3)'
        ]
        executor= self.runit(listing)
        self.assertEqual(4, executor.get_symbol_count()-executor._builtin_count)
        Z = executor.get_symbol("Z")
        self.assertEqual(110, Z)

    def test_builtin_int(self):
        listing = [
            '90 A=INT(1.99)',
        ]
        executor= self.runit(listing)
        self.assertEqual(1, executor.get_symbol_count()-executor._builtin_count)
        A = executor.get_symbol("A")
        self.assertEqual(1, A)

    def test_builtin_rnd(self):
        listing = [
            '90 A=RND(1)',
        ]
        executor= self.runit(listing)
        self.assertEqual(1, executor.get_symbol_count()-executor._builtin_count)
        A = executor.get_symbol("A")
        self.assertTrue(A > 0 and A < 1.0)


    def test_expressions(self):
        listing = [
            '100 A =2+1',
            '110 B=4',
            '120 C = A + B',
            '130 D$="ABC"',
            '140 E$=D$+"DEF"',
        ]
        executor= self.runit(listing)
        self.assertEqual(5, executor.get_symbol_count()-executor._builtin_count)
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

    def test_expressions2(self):
        listing = [
            '100 A =2+1',
            '110 B=A/2',
        ]
        executor= self.runit(listing)
        self.assertEqual(2, executor.get_symbol_count()-executor._builtin_count)
        A = executor.get_symbol("A")
        B = executor.get_symbol("B")
        self.assertEqual(A, 3)
        self.assertEqual(B, 1.5)

    def test_expressions3(self):
        listing = [
            '100 A=2+"1"',
        ]
        executor= self.runit_se(listing)

    def test_goto(self):
        listing = [
            '100 GOTO 130',
            '110 A=1',
            '120 GOTO 140',
            '130 B  = 2',
            '140 END',
        ]
        executor= self.runit(listing)
        self.assertEqual(1, executor.get_symbol_count()-executor._builtin_count)
        B = executor.get_symbol("B")
        self.assertEqual(B, 2)

    def test_goto2(self):
        listing = [
            '100 A=3:GOTO 120:A=4',
            '120 B=4000',
        ]
        executor= self.runit(listing)
        self.assertEqual(2, executor.get_symbol_count()-executor._builtin_count)
        A = executor.get_symbol("A")
        self.assertEqual(A, 3)
        B = executor.get_symbol("B")
        self.assertEqual(B, 4000)

    def test_assignment(self):
        listing = [
            '100 A=5:B=6',
            '110 A= A+A',
            '120 B= B*A',
        ]
        executor= self.runit(listing)
        self.assertEqual(2, executor.get_symbol_count()-executor._builtin_count)
        self.assert_value(executor, "A", 10)
        self.assert_value(executor, "B", 60)


    def test_gosub(self):
        listing = [
            '100 A=5: GOSUB 1000',
            '120 B=4000',
            '130 END',
            '1000 REM Subroutine',
            '1010 A= A+A',
            '1020 RETURN',
        ]
        executor= self.runit(listing)
        self.assertEqual(2, executor.get_symbol_count()-executor._builtin_count)
        self.assert_value(executor, "A", 10)
        self.assert_value(executor, "B", 4000)


    def test_end(self):
        listing = [
            '100 END',
            '110 A$="1"',
            '130 B  = 2',
        ]
        executor= self.runit(listing)
        self.assertEqual(0, executor.get_symbol_count()-executor._builtin_count)

    def test_print(self):
        listing = [
            '100 PRINT "SHOULD SEE THIS"'
        ]
        executor, program_output = self.runit_capture(listing)
        self.assertEqual('SHOULD SEE THIS\n', program_output)

        listing = [
            '90 K9=12',
            '100 PRINT"     DESTROY THE";K9;"KLINGON WARSHIPS WHICH HAVE INVADED"'
        ]
        executor, program_output = self.runit_capture(listing)
        self.assertEqual('     DESTROY THE 12 KLINGON WARSHIPS WHICH HAVE INVADED\n', program_output)

    def test_suite_dim(self):
        """
        Tests with "suite" in the name test for errors.
        :return:
        """
        program = tokenize(['100 DIM A(8'])
        self.assertEqual(1, len(program))
        executor = Executor(program)
        with self.assertRaises(BasicSyntaxError):
            executor.run_program()

        # Assert they gave it a dim May not be right, some dialoects of basic assume 10
        program = tokenize(['100 DIM C'])
        self.assertEqual(1, len(program))
        executor = Executor(program)
        with self.assertRaises(BasicSyntaxError):
            executor.run_program()

    def test_array_assignment_error(self):
        listing = [
            '110 A(3,2=1',
        ]
        with self.assertRaises(BasicSyntaxError):
            executor= self.runit(listing)

    def test_array_assignment_error2(self):
        listing = [
            '110 A()=1',
        ]
        with self.assertRaises(BasicSyntaxError):
            executor= self.runit(listing)

    def test_array_assignment_error3(self):
        listing = [
            '110 A(1,2,3)=1',
        ]
        with self.assertRaises(BasicSyntaxError):
            executor= self.runit(listing)

    def test_array_assignment_error4(self):
        # Array not initialized. Some basics allow this. For now, we don't
        listing = [
            '110 A(1)=1',
        ]
        with self.assertRaises(BasicSyntaxError):
            executor= self.runit(listing)

    def test_array_assignment1(self):
        listing = [
            '100 DIMA(10)',
            '110 A(3)=17',
        ]
        executor= self.runit(listing)
        A = executor.get_symbol("A")
        # TODO Figure out if the language expects zero-based arrays, or one based.
        # It looks like "startrek.bas" expects zero based, and superstartrek.bas expects 1
        # TODO Add an option. Add a getter to Executor, so the test can be independent.
        # TODO Need to handle array access in expressions. Including D$(1,2)
        self.assertEqual(0, A[0], 0) # Check for initialization
        self.assertEqual(17, A[3])   # Verify assignment

    # TODO Need multi-dimensional array support in expression evaluation
    # def test_array_assignment2(self):
    #     listing = [
    #         '100 DIMA(10)',
    #         '110 A(3)=27',
    #         '120 Y=A(3)',
    #         '200 DIM B( 10, 5)',
    #         '110 B(1, 4)=17',
    #         '120 Z=B(1,5)'
    #     ]
    #     executor= self.runit(listing)
    #     A = executor.get_symbol("A")
    #     B = executor.get_symbol("B")
    #     Y = executor.get_symbol("Y")
    #     Z = executor.get_symbol("Z")
    #     # TODO Figure out if the language expects zero-based arrays, or one based.
    #     # It looks like "startrek.bas" expects zero based, and superstartrek.bas expects 1
    #     # TODO Add an option. Add a getter to Executor, so the test can be independent.
    #     # TODO Need to handle array access in expressions. Including D$(1,2)
    #     self.assertEqual(A[0], 0) # Check for initialization
    #     self.assertEqual(A[3], 27) # Verify assignment
    #     self.assertEqual(Z, 3) # Verify element access
    #     # TODO two dimensional arrays.

    def test_array_assignment3(self):
        listing = [
            '100 DIMA(10)',
            '110 A(3)=27',
            '120 Y=A(3)',
        ]
        executor= self.runit(listing)
        A = executor.get_symbol("A")
        Y = executor.get_symbol("Y")
        # TODO Figure out if the language expects zero-based arrays, or one based.
        # It looks like "startrek.bas" expects zero based, and superstartrek.bas expects 1
        # TODO Add an option. Add a getter to Executor, so the test can be independent.
        # TODO Need to handle array access in expressions. Including D$(1,2)
        self.assertEqual(A[0], 0) # Check for initialization
        self.assertEqual(A[3], 27) # Verify assignment
        self.assertEqual(27, Y) # Verify element access
        # TODO two dimensional arrays.

    def test_is_valid_variable(self):
        is_valid_identifier("A")
        is_valid_identifier("B1")
        is_valid_identifier("B1$")
        with self.assertRaises(BasicSyntaxError):
            executor= is_valid_identifier("LONG")
        with self.assertRaises(BasicSyntaxError):
            executor= is_valid_identifier("1A")
        with self.assertRaises(BasicSyntaxError):
            executor= is_valid_identifier("1$$")

    def test_if(self):
        # 'IFR1>.98THENK3=3:K9=K9+3:GOTO980'
        # "IFW1>0ANDW1<=8THEN2490"
        listing = [
            '100 R1=1.0',
            '110 K3=-1',
            '120 IFR1>.98THENK3=12',
        ]
        executor= self.runit(listing)
        self.assert_value(executor,"K3", 12)

    def test_if2(self):
        # TODO we don't handle nested if thens
        # ALSO, startrek.bas has ELSE.
        # 'IFR1>.98THENK3=3:K9=K9+3:GOTO980'
        # "IFW1>0ANDW1<=8THEN2490"
        listing = [
            '100 R1=1.0',
            '110 K3=-1',
            '120 IFR1>.98THENK3=12',
        ]
        executor= self.runit(listing)
        self.assert_value(executor,"K3", 12)


    def test_if_not(self):
        # Test if condition is false in IF THEN
        listing = [
            '100 A=1.0:B=2:C=3:D=4',
            '120 IFA<.98THENB=12'
        ]
        executor= self.runit(listing)
        self.assert_value(executor, "B", 2)

    def test_if_nested(self):
        # Test if condition is false in IF THEN
        listing = [
            '100 A=1.0:B=2:C=3:D=4:F=-1',
            '120 IFA>.98THENB=12:IF B>1THENE=17',
            '130 IFA>.98THENB=12:IF B<1THENF=5555'
        ]
        executor= self.runit(listing)
        self.assert_values(executor, {"B":12, "E":17, "F":-1})

    def test_if_se(self):
        listing = [
            '100 IF I > 0'
        ]
        executor= self.runit_se(listing)

    def test_order_se(self):
        listing = [
            '100 REM ',
            '100 REM'
        ]
        executor= self.runit_se(listing)

    def test_not_equals(self):
        listing = [
            '100 X=1',
            '110 IF3<>2THENX=3',
            '120 IF3<>3THENX=5'
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "X", 3)

    def test_and(self):
        listing = [
            '100 X=10:Y=3',
            '110 IFX>YANDY>0THENA=9', # True, True => True
            '120 IFX>YANDY<0THENB=10', # True, False => False
            '130 IFX<YANDY>0THENC=11', # False, True => False
            '140 IFX<YANDY<0THEND=12', # False, False => False
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "X", 10)
        self.assert_value(executor, "Y", 3)
        self.assert_value(executor, "A", 9)
        self.assertFalse(executor.is_symbol_defined("B"))
        self.assertFalse(executor.is_symbol_defined("C"))
        self.assertFalse(executor.is_symbol_defined("D"))

    def test_or(self):
        listing = [
            '100 X=10:Y=3',
            '110 IFX>YORY>0THENA=9', # True, True => True
            '120 IFX>YORY<0THENB=10', # True, False => True
            '130 IFX<YORY>0THENC=11', # False, True => True
            '140 IFX<YORY<0THEND=12', # False, False => False
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "X", 10)
        self.assert_value(executor, "Y", 3)
        self.assert_value(executor, "A", 9)
        self.assert_value(executor, "B", 10)
        self.assert_value(executor, "C", 11)
        self.assertFalse(executor.is_symbol_defined("D"))

