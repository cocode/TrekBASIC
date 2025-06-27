"""
Some basic tests. It's not ideal, we have some test of loading, and some tests of executing
"""

from io import StringIO
from unittest import TestCase
import sys
from math import e

from basic_dialect import ARRAY_OFFSET
from basic_interpreter import Executor
from basic_statements import is_valid_identifier
from basic_types import SymbolType, RunStatus, lexer_token, BasicSyntaxError
from basic_loading import tokenize


class Test(TestCase):
    def assert_value(self, executor: Executor, symbol: str, expected_value):
        """
        Asserts the that symbol has the expected value

        THIS ONLY CHECKS THE SYMBOL TABLE SymbolTable.VARIABLE, not ARRAY, or FUNCTION
        :param executor:
        :param symbol:
        :param expected_value:
        :return:
        """
        value = executor.get_symbol(symbol)
        self.assertEqual(expected_value, value)

    def assert_values(self, executor: Executor, expected_values):
        """
        Verifies the symbol table contains the values passed in.
        Does NOT check for extra values.
        :param executor:
        :param expected_values: dict of {var:value}
        :return: None. Raises an exception, if needed.
        """
        for item in expected_values.items():
            self.assert_value(executor, item[0], item[1])

    def runit(self, listing, trace_file=None):
        program = tokenize(listing)
        self.assertEqual(len(listing), len(program))
        executor = Executor(program, trace_file=trace_file, stack_trace=True)
        executor.run_program()
        return executor

    def runit_capture(self, listing, input=None):
        """
        Run the program, but capture the output, instead of printing it.
        This allows us to verify the output in tests, and it also can be
        used just to keep the output from littering the test output.
        """
        old = sys.stdout
        output = StringIO()
        sys.stdout = output
        if input is not None:
            old_input = sys.stdin
            sys.stdin = input
        try:
            executor = self.runit(listing)
        finally:
            sys.stdout = old
            if input is not None:
                sys.stdin = old_input

        program_output = output.getvalue()
        return executor, program_output

    def runit_se(self, listing):
        """
        Run, and verify that the program raises a BasicSyntaxError
        :param listing:
        :return:
        """
        with self.assertRaises(BasicSyntaxError):
            executor = self.runit_capture(listing)

    def test_assignment(self):
        # Also verifies strings do not have their case changed,
        executor = self.runit(['100 Z$="Fred"'])
        self.assertEqual(1, executor.get_symbol_count())
        self.assertEqual('Fred', executor.get_symbol("Z$"))

    def test_assignment_1(self):
        listing = [
            '100 A=5:B=6',
            '110 A= A+A',
            '120 B= B*A',
        ]
        executor = self.runit(listing)
        self.assertEqual(2, executor.get_symbol_count())
        self.assert_value(executor, "A", 10)
        self.assert_value(executor, "B", 60)

    def test_assignment2(self):
        program = ['100 TOOLONGVARNAME="Fred"']
        self.assertEqual(1, len(program))
        self.runit_se(program)

    def test_dim(self):
        executor = self.runit(['100 DIM A(8), C(3, 2)'])
        self.assertEqual(2, executor.get_symbol_count())
        A = executor.get_symbol("A", SymbolType.ARRAY)
        C = executor.get_symbol("C", SymbolType.ARRAY)
        self.assertEqual(8, len(A))
        self.assertEqual(3, len(C))
        self.assertEqual(2, len(C[0]))

    def test_def(self):
        executor = self.runit(['100 DEF FNA(X)=X^2+1'])
        self.assertEqual(1, executor.get_symbol_count())
        # self.assert_value(executor, "FNA", "X^2+1")
        value = executor.get_symbol("FNA", symbol_type=SymbolType.FUNCTION)
        expected = [lexer_token(token='X', type='id'),
                    lexer_token(token='^', type='op'),
                    lexer_token(token=2.0, type='num'),
                    lexer_token(token='+', type='op'),
                    lexer_token(token=1.0, type='num')]
        self.assertEqual(expected, value)

        AT = executor.get_symbol_type("FNA", SymbolType.FUNCTION)
        self.assertEqual(SymbolType.FUNCTION, AT)

    def test_def2(self):
        listing = [
            '100 DEF FNA(X)=X^2+1',
            '110 Y=FNA(5)',
            '120 Z=FNA(7*7)',
        ]
        executor = self.runit(listing)
        self.assertEqual(3, executor.get_symbol_count())
        self.assert_value(executor, "Y", 26)
        self.assert_value(executor, "Z", 2402)

    def test_def3(self):
        listing = [
            '90 A=2+1',
            '100 DEF FNA(X)=X^A+1',
            '110 Y=FNA(5)',
            '120 Z=FNA(A*A)',
        ]
        executor = self.runit(listing)
        self.assertEqual(4, executor.get_symbol_count())
        self.assert_value(executor, "Y", 126)
        self.assert_value(executor, "Z", 730)

    def test_def4(self):
        listing = [
            '100 DEF FNA(X)=X^2',
            '110 DEF FNB(X)=2*X+3',
            '120 DEF FNC(X)=FNA(3*X)+FNB(X+1)',
            '130 Z=FNC(3)'
        ]
        executor = self.runit(listing)
        self.assertEqual(4, executor.get_symbol_count())
        self.assert_value(executor, "Z", 92)

    def test_def5(self):
        listing = [
            '100 DEF FNA(X)=X^2',  # 16, 36
            '110 DEF FNB(X)=2*FNA(X)+3',  # 35, 75
            '120 X=FNB(4)',
            '130 Y=FNB(6)',  # 110
            '140 Z=X+Y'
        ]
        executor = self.runit(listing)
        self.assertEqual(5, executor.get_symbol_count())
        self.assert_value(executor, "Z", 110)

    def test_def6(self):
        listing = [
            '100 DEF FNA(X)=X^2',  # 16, 36
            '110 DEF FNB(X)=2*FNA(X)+3',  # 35, 75
            '120 DEF FNC(X)=FNB(X+1)+FNB(X*2)',  # 110
            '130 Z=FNC(3)'
        ]
        executor = self.runit(listing)
        self.assertEqual(4, executor.get_symbol_count())
        self.assert_value(executor, "Z", 110)

    def test_builtin_int(self):
        listing = [
            '90 A=INT(1.99)',
        ]
        executor = self.runit(listing)
        self.assertEqual(1, executor.get_symbol_count())
        self.assert_value(executor, "A", 1)

    def test_builtin_rnd(self):
        listing = [
            '90 A=RND(1)',
        ]
        executor = self.runit(listing)
        self.assertEqual(1, executor.get_symbol_count())
        A = executor.get_symbol("A")
        self.assertTrue(A > 0 and A < 1.0)

    def test_builtin_sgn(self):
        listing = [
            '1000 A=SGN(1)',
            '1010 B=SGN(-3711)',
            '1020 C=SGN(0)',
        ]
        executor = self.runit(listing)
        self.assertEqual(3, executor.get_symbol_count())
        self.assert_value(executor, "A", 1)
        self.assert_value(executor, "B", -1)
        self.assert_value(executor, "C", 0)

    def test_builtin_exp(self):
        listing = [
            '10000 A=EXP(1)',
        ]
        executor = self.runit(listing)
        self.assertEqual(1, executor.get_symbol_count())
        self.assert_value(executor, "A", e)

    def test_expressions(self):
        listing = [
            '100 A =2+1',
            '110 B=4',
            '120 C = A + B',
            '130 D$="ABC"',
            '140 E$=D$+"DEF"',
        ]
        executor = self.runit(listing)
        self.assertEqual(5, executor.get_symbol_count())
        self.assert_value(executor, "A", 3)
        self.assert_value(executor, "B", 4)
        self.assert_value(executor, "C", 7)
        self.assert_value(executor, "D$", "ABC")
        self.assert_value(executor, "E$", "ABCDEF")

    def test_expressions2(self):
        listing = [
            '100 A =2+1',
            '110 B=A/2',
        ]
        executor = self.runit(listing)
        self.assertEqual(2, executor.get_symbol_count())
        A = executor.get_symbol("A")
        B = executor.get_symbol("B")
        self.assertEqual(A, 3)
        self.assertEqual(B, 1.5)

    def test_expressions3(self):
        listing = [
            '100 A=2+"1"',
        ]
        self.runit_se(listing)

    def test_goto(self):
        listing = [
            '100 GOTO 130',
            '110 A=1',
            '120 GOTO 140',
            '130 B  = 2',
            '140 END',
        ]
        executor = self.runit(listing)
        self.assertEqual(1, executor.get_symbol_count())
        self.assertFalse(executor.is_symbol_defined("A"))
        self.assert_value(executor, "B", 2)

    def test_goto2(self):
        listing = [
            '100 A=3:GOTO 120:A=4',
            '120 B=4000',
        ]
        executor = self.runit(listing)
        self.assertEqual(2, executor.get_symbol_count())
        self.assert_value(executor, "A", 3)
        self.assert_value(executor, "B", 4000)

    def test_gosub(self):
        listing = [
            '100 A=5: GOSUB 1000',
            '120 B=4000',
            '130 END',
            '1000 REM Subroutine',
            '1010 A= A+A',
            '1020 RETURN',
        ]
        executor = self.runit(listing)
        self.assertEqual(2, executor.get_symbol_count())
        self.assert_value(executor, "A", 10)
        self.assert_value(executor, "B", 4000)

    def test_end(self):
        listing = [
            '100 END',
            '110 A$="1"',
            '130 B  = 2',
        ]
        executor = self.runit(listing)
        self.assertEqual(0, executor.get_symbol_count())

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
        program = ['100 DIM A(8']
        self.assertEqual(1, len(program))
        self.runit_se(program)

        # Assert they gave it a dim May not be right, some dialoects of basic assume 10
        program = ['100 DIM C']
        self.runit_se(program)

    def test_array_assignment_error(self):
        listing = [
            '110 A(3,2=1',
        ]
        with self.assertRaises(BasicSyntaxError):
            executor = self.runit(listing)

    def test_array_assignment_error2(self):
        listing = [
            '110 A()=1',
        ]
        with self.assertRaises(BasicSyntaxError):
            executor = self.runit(listing)

    def test_array_assignment_error3(self):
        listing = [
            '110 A(1,2,3)=1',
        ]
        with self.assertRaises(BasicSyntaxError):
            executor = self.runit(listing)

    def test_array_assignment_error4(self):
        # Array is not initialized. Some basics allow this. For now, we don't
        listing = [
            '110 A(1)=1',
        ]
        with self.assertRaises(BasicSyntaxError):
            executor = self.runit(listing)

    def test_array_assignment1(self):
        listing = [
            '100 DIMA(10)',
            '110 A(3)=17',
        ]
        executor = self.runit(listing)
        A = executor.get_symbol("A", SymbolType.ARRAY)
        # It looks like "startrek.bas" expects zero-based arrays, and superstartrek.bas expects 1
        self.assertEqual(0, A[0], 0)  # Check for initialization
        self.assertEqual(17, A[3-ARRAY_OFFSET])   # Verify assignment.

    def test_array_assignment2(self):
        listing = [
            '100 DIMA(10)',
            '105 I5=2*3',
            '110 A(I5)=I5+1',
        ]
        executor = self.runit(listing)
        A = executor.get_symbol("A", SymbolType.ARRAY)
        self.assertEqual(0, A[0], 0)  # Check for initialization
        self.assertEqual(7, A[6-ARRAY_OFFSET])   # Verify assignment

    def test_array_assignment3(self):
        listing = [
            '100 DIMA(10)',
            '110 A(3)=7',
            '120 Y=A(3)+1',
            '200 DIM B( 10, 5)',
            '210 B(1, 4)=Y*2',
            '220 Z=B(1,4)+3'
        ]
        executor = self.runit(listing)
        A = executor.get_symbol_value("A", SymbolType.ARRAY)
        B = executor.get_symbol_value("B", SymbolType.ARRAY)
        Y = executor.get_symbol_value("Y", SymbolType.VARIABLE)
        Z = executor.get_symbol_value("Z", SymbolType.VARIABLE)

        self.assertEqual(A[0], 0)  # Check for initialization
        self.assertEqual(A[3-ARRAY_OFFSET], 7)  # Verify assignment
        self.assertEqual(Y, 8)  # Verify element access
        self.assertEqual(B[0][3], 16)  # Verify element access
        self.assertEqual(Z, 19)  # Verify element access

    def test_array_assignment4(self):
        listing = [
            '100 DIMA(2,3,4)',
            '110 A(1,2,3)=27',
            '120 A(1,2,1)=6',
            '130 Y=A(1,2,3)+1',
            '140 Z=A(1,2,1)-1',
        ]
        executor = self.runit(listing)
        A = executor.get_symbol("A", SymbolType.ARRAY)
        Y = executor.get_symbol("Y", SymbolType.VARIABLE)
        Z = executor.get_symbol("Z", SymbolType.VARIABLE)
        self.assertEqual(0, A[0][0][0])  # Check for initialization
        self.assertEqual(27, A[1-ARRAY_OFFSET][2-ARRAY_OFFSET][3-ARRAY_OFFSET])  # Verify assignment
        self.assertEqual(6, A[1-ARRAY_OFFSET][2-ARRAY_OFFSET][1-ARRAY_OFFSET])  # Verify array rows aren't all the same.
        self.assertEqual(28, Y)  # Verify element access
        self.assertEqual(5, Z)  # Verify element access

    def test_is_valid_variable(self):
        is_valid_identifier("A")
        is_valid_identifier("B1")
        is_valid_identifier("B1$")
        with self.assertRaises(BasicSyntaxError):
            is_valid_identifier("LONG")
        with self.assertRaises(BasicSyntaxError):
            executor = is_valid_identifier("1A")
        with self.assertRaises(BasicSyntaxError):
            executor = is_valid_identifier("1$$")

    def test_if(self):
        # 'IFR1>.98THENK3=3:K9=K9+3:GOTO980'
        # "IFW1>0ANDW1<=8THEN2490"
        listing = [
            '100 R1=1.0',
            '110 K3=-1',
            '120 IFR1>.98THENK3=12',
            '130 IFR1<.98THENK4=15',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "K3", 12)
        self.assertFalse(executor.is_symbol_defined("K4"))

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
        executor = self.runit(listing)
        self.assert_value(executor, "K3", 12)

    def test_if_not(self):
        # Test if condition is false in IF THEN
        listing = [
            '100 A=1.0:B=2:C=3:D=4',
            '120 IFA<.98THENB=12'
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "B", 2)

    def test_if_nested(self):
        # Test if condition is false in IF THEN
        listing = [
            '100 A=1.0:B=2:C=3:D=4:F=-1',
            '120 IFA>.98THENB=12:IF B>1THENE=17',
            '130 IFA>.98THENB=12:IF B<1THENF=5555'
        ]
        executor = self.runit(listing)
        self.assert_values(executor, {"B": 12, "E": 17, "F": -1})

    def test_if_se(self):
        listing = [
            '100 IF I > 0'
        ]
        self.runit_se(listing)

    def test_order_se(self):
        listing = [
            '100 REM ',
            '100 REM'
        ]
        self.runit_se(listing)

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
            '110 IFX>YANDY>0THENA=9',  # True, True => True
            '120 IFX>YANDY<0THENB=10',  # True, False => False
            '130 IFX<YANDY>0THENC=11',  # False, True => False
            '140 IFX<YANDY<0THEND=12',  # False, False => False
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
            '110 IFX>YORY>0THENA=9',  # True, True => True
            '120 IFX>YORY<0THENB=10',  # True, False => True
            '130 IFX<YORY>0THENC=11',  # False, True => True
            '140 IFX<YORY<0THEND=12',  # False, False => False
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "X", 10)
        self.assert_value(executor, "Y", 3)
        self.assert_value(executor, "A", 9)
        self.assert_value(executor, "B", 10)
        self.assert_value(executor, "C", 11)
        self.assertFalse(executor.is_symbol_defined("D"))

    # For loop tests
    #   Simple 1..10
    #   Nested
    #   FOR and NEXT in the middle of different lines.
    #   Check the we detect mismatch loop indices.
    #   STEP other than 1
    # TODO
    # O. Need some way to tell if this is the first time I've started the for, or if we are comnig back from the next!
        # Could split it into two statements: I=1:FOR TO 10 STEP 1 and have the next to the modified FOR stmt.
    # 1. add a for / next stack to executor
    # 2. add a for method to start a for to the executor
    # 3. add a next method to the exector
    #    add a custom statement parser for FOR.
    # 4. Make stmt_for and stmt_next
    # 5. start, and and step can all be expressions.
    # 6. According to quitebasic.com, you can change the step and end values while the loop is running, but not the start.
#     10 LET j=10
# 100 for i = 1 to j step 2
# 110 LET j = j + 1
# 115 print i;" ";j
# 120 next i
    def test_for(self):
        listing = [
            '100 J=0:FOR I=1TO10',
            '110 J=J+2',
            '120 NEXTI',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "I", 11)
        self.assert_value(executor, "J", 20)

    def test_for_nested(self):
        listing = [
            '100 K=0:FOR I=1TO10:FOR J = 1 TO 10',
            '110 K=K+2',
            '120 NEXTJ:NEXTI',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "I", 11)  # I think this is not visible in basic, but probably depends on dialect
        self.assert_value(executor, "J", 11)
        self.assert_value(executor, "K", 200)

    def test_get_next_stmt(self):
        listing = [
            '100 J=0:FOR I=1TO10',
            '110 J=J+2',
            '120 NEXTI',
        ]
        program = tokenize(listing)
        self.assertEqual(len(listing), len(program))
        executor = Executor(program)
        ct = executor.get_next_stmt()
        self.assertEqual(0, ct.index)
        self.assertEqual(1, ct.offset)

    def test_on_goto(self):
        listing = [
            '100 J=2:ONJGOTO200,300,400',
            '200 K=200:GOTO500',
            '300 K=300:GOTO500',
            '400 K=400:GOTO500',
            '500 END',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "K", 300)

    def test_on_goto_2(self):
        listing = [
            '100 Z4=4:Z5=8',
            '9030 IFZ5<=4THENONZ4GOTO9040,9050,9060,9070,9080,9090,9100,9110',
            '9035 GOTO9120',
            '9040 G2$="ANTARES":GOTO9210',
            '9050 G2$="RIGEL":GOTO9210',
            '9060 G2$="PROCYON":GOTO9210',
            '9070 G2$="VEGA":GOTO9210',
            '9080 G2$="CANOPUS":GOTO9210',
            '9090 G2$="ALTAIR":GOTO9210',
            '9100 G2$="SAGITTARIUS":GOTO9210',
            '9110 G2$="POLLUX":GOTO9210',
            '9120 REM',
            '9210 END'
        ]
        executor = self.runit(listing)
        self.assertFalse(executor.is_symbol_defined("G2$"))

    def test_on_gosub(self):
        listing = [
            '100 J=2:ONJGOSUB200,300,400',
            '110 Q=77',
            '120 END',
            '200 K=200:RETURN',
            '300 K=300:RETURN',
            '400 K=400:RETURN',
            '500 END',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "J", 2)
        self.assert_value(executor, "K", 300)
        self.assert_value(executor, "Q", 77)

    def test_input_1(self):
        listing = [
            '100 INPUT"ENTER YES:";A1$',
        ]
        executor, output = self.runit_capture(listing, input=StringIO("YES"))
        self.assertEqual("ENTER YES:", output)
        self.assertEqual('YES', executor.get_symbol_value("A1$"))

    def test_input_2(self):
        # You have to type in the answer!! There is no prompt.
        listing = [
            '110 INPUT "ENTER 59:";A'
        ]
        executor, output = self.runit_capture(listing, input=StringIO("59"))
        self.assertEqual("ENTER 59:", output)
        self.assertEqual(59, executor.get_symbol_value("A"))

    def test_input_3(self):
        listing = [
            '110 INPUTW1'
        ]
        executor, output = self.runit_capture(listing, input=StringIO("91"))
        self.assertEqual("", output)
        self.assertEqual(91, executor.get_symbol_value("W1"))

    def test_input_4(self):
        listing = [
            '110 INPUT "ENTER 1,22:";X,Y'
        ]
        executor, output = self.runit_capture(listing, input=StringIO("1,22"))
        self.assertEqual(1, executor.get_symbol_value("X"))
        self.assertEqual(22, executor.get_symbol_value("Y"))

    def test_line_numbers(self):
        # You have to type in the answer!!
        listing = [
            '''PRINT "THIS WON'T WORK"'''
        ]
        self.runit_se(listing)

    def test_clear(self):
        listing = [
            '1000 A=3',
            '1010 CLEAR 1000',
        ]
        executor = self.runit(listing)
        self.assertEqual(0, executor.get_symbol_count())
        self.assertFalse(executor.is_symbol_defined("A"))

    def test_array_access(self):
        listing = [
            '1000 DIMA(2)',
            '1010 B=A(1)',
            '1020 DIMC(2,3)',
            '1030 C(1,2)=37',
            '1040 D=C(1,2)',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "B", 0)
        self.assert_value(executor, "D", 37)

    def test_array_access_error(self):
        listing = [
            '1000 DIMA(2)',
            '1030 D=A(1,2)',  # Too many dimensions
        ]
        self.runit_se(listing)

    def test_example_0(self):
        listing = [
            '1030 K3=0',
            '1540 IFK3=0THEN1590',
            '1550 K3=9',
            '1590 END'
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "K3", 0)

    def test_int_dup(self):
        listing = [
            '1030 I=INT(10.5)',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "I", 10)

    def test_left(self):
        listing = [
            '1540 Z$=LEFT$("ABCDEFGHI", 3)',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "Z$", "ABC")

    def test_right(self):
        listing = [
            '1540 Z$=RIGHT$("ABCDEFGHI", 3)',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "Z$", "GHI")

    def test_mid(self):
        listing = [
            '1540 Z$=MID$("ABCDEFGHI", 4, 3)',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "Z$", "DEF")

    def test_mid_2(self):
        listing = [
            '1540 Z$=MID$("ABCDEFGHI", 4)',
        ]
        self.runit_se(listing)

    def test_str_dollar(self):
        listing = [
            '1540 Z$=STR$(3+4)',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "Z$", "7")

    def test_abs(self):
        listing = [
            '1540 Z=ABS(-3*4)',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "Z", 12)

    def test_space_dollar(self):
        listing = [
            '1540 Z$=SPACE$(3+4)',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "Z$", "       ")

    def test_len(self):
        listing = [
            '1000 A$="TOM"',
            '1040 A=LEN(A$)',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "A$", "TOM")
        self.assert_value(executor, "A", 3)

    def test_example_1(self):
        listing = [
            '100 DIMC(9,2)',
            "530 FORI=1TO9:C(I,1)=I:C(I,2)=I+7:NEXTI"
        ]
        executor = self.runit(listing)
        C = executor.get_symbol("C", SymbolType.ARRAY)
        self.assertEqual([3, 10], C[2])

    def test_example_2(self):
        listing = [
            '100 E=100:S=10:DIMD(7)',
            '1990 IFS+E>10THENIFE>10ORD(7)=0THEN2060',
            '2000 A=6:END',
            '2060 A=5:END'
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "A", 5)

    def test_example_3(self):
        listing = [
            '1000 B9=0',
            "1630 IF B9<>0 THEN 1690",
            '1690 A=5:END'
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "A", 5)

    def test_example_4(self):
        listing = [
            '1000 S=0:E=3000:DIMD(8):D(7)=0',
            '2160 IF S+E>10 THEN IF E>10 OR D(7)=0 THEN 2240',
            '2165 PRINT "WRONG!"',
            '2170 A=5:END',
            '2240 A=-9999',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "A", -9999)

    # # It turns out basic DOES NOT have ORD, so I don't have this issue.
    # # It still points out a weakness in my lexing.
    # def test_example_5(self):
    #     listing = [
    #         '2260 X$=CHR$(32)',
    #         '2270 C=ORD(X$)'
    #     ]
    #     executor = self.runit(listing)
    #     self.assert_value(executor, "X$", " ")
    #     self.assert_value(executor, "C", 32)

    # Not implemented yet. Waiting for ELSE support
    #
    # def test_example_6(self):
    #     listing = [
    #         '2240 INPUT "Command ";A$',
    #         '2250 IF LEN(A$)=0 THEN 2320',
    #         '2260 X$=""',
    #         '2270 FOR I=1 TO LEN(A$)',
    #         '2280 C$=MID$(A$,I,1)',
    #         '2290 IF C$>="a" AND C$<="z" THEN X$=X$+CHR$(ASC(C$)-32) ELSE X$=X$+C$',
    #         '2300 NEXT I',
    #     ]
    #     executor = self.runit(listing)
    #     self.assert_value(executor, "A", -9999)

    def test_run_status(self):
        executor = self.runit(['1000 A=3'])
        self.assertEqual(RunStatus.END_OF_PROGRAM, executor._run)
        executor = self.runit(['1000 A=3:END:A=4'])
        self.assertEqual(RunStatus.END_CMD, executor._run)
        # Check case of IF on last line, with a False condition
        executor = self.runit(['1000 A=3:A=4:IFA=3THENGOTO1000'])
        self.assertEqual(RunStatus.END_OF_PROGRAM, executor._run)
        # Syntax Error
        self.runit_se(['1000 A='])

    def test_run_status2(self):
        program = tokenize(['1000 A=3:ERROR'])
        executor = Executor(program)
        try:
            executor.run_program()
        except:
            pass
        self.assertEqual(RunStatus.END_ERROR_INTERNAL, executor._run)

    def test_array_access_1(self):
        listing = [
            '1000 DIMA(3)',
            '2160 X=A(3)',
            '2170 A(2)=17',
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "X", 0)
        A = executor.get_symbol("A", SymbolType.ARRAY)
        self.assertTrue(A[1] == 17)

    def test_array_names(self):
        # Test to see that array names don't conflict with scalar variable names.
        listing = [
            '1000 S=-17:DIMS(8)',
            "2160 FORI=1TO8:S(I)=I*I:NEXTI",
        ]
        executor = self.runit(listing)
        self.assert_value(executor, "S", -17)
        S = executor.get_symbol("S", SymbolType.ARRAY)
        for i in range(0, 8):
            self.assertTrue(S[i] == (i+1)*(i+1))

