"""
This will be the base for all test cases we do.
It has some utilities that are used by many of the tests
"""

from io import StringIO
from unittest import TestCase
import sys

from trekbasicpy.basic_interpreter import Executor
from trekbasicpy.basic_types import BasicSyntaxError, BasicRuntimeError
from trekbasicpy.basic_loading import tokenize


class TestCaseBase(TestCase):
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

    def runit_re(self, listing):
        """
        Run, and verify that the program raises a BasicSyntaxError
        :param listing:
        :return:
        """
        with self.assertRaises(BasicRuntimeError):
            executor = self.runit_capture(listing)
