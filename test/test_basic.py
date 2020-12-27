from io import StringIO
from unittest import TestCase
import sys

from basic_interpreter import Executor
from basic_types import BasicSyntaxError
from basic_loading import tokenize
import basic


class Test(TestCase):
    def assert_value(self, executor:Executor, symbol:str, expected_value):
        value = executor.get_symbol(symbol)
        self.assertEqual(expected_value, value)

    def assert_values(self, executor:Executor, expected_values):
        """
        Verifies the symbol table contains the values passed in.
        Does NOT check for extra values.
        :param executor:
        :param expected_values: dict of {var:value}
        :return: None. Raises an exception, if needed.
        """
        for item in expected_values.items():
            self.assert_value(executor, item[0], item[1])


    def runit(self, listing, trace=False):
        program = tokenize(listing)
        self.assertEqual(len(listing), len(program))
        executor = Executor(program, trace=trace, stack_trace=True)
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

    def test_trace(self):
        # This doesn't actually test the output, but it's handy to have for debugging trace.
        listing = [
            '100 PRINT:PRINT:PRINT:PRINT',
            '110 J=3+2',
            '120 PRINTJ',
        ]
        program = tokenize(listing)
        self.assertEqual(len(listing), len(program))
        with open("tracefile.txt", "w") as f:
            executor = Executor(program, trace_file=f)
            executor.run_program()

