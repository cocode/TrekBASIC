import os
from io import StringIO
from unittest import mock

from trekbasicpy.basic import find_program_file
from trekbasicpy.basic_interpreter import Executor
from trekbasicpy.basic_loading import tokenize
from trekbasicpy.basic_utils import TRACE_FILE_NAME
from test.test_case_base import TestCaseBase
import tempfile


class Test(TestCaseBase):
    def test_find_program_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".bas", delete=True) as temp_file:
            print(f"Temporary file created: {temp_file.name}")
            temp_file.write(b'10 PRINT "HELLO"\n20 END\n')
            temp_file.flush()
            path_no_ext, _ = os.path.splitext(temp_file.name)
            xx = find_program_file(path_no_ext)
            self.assertEqual(temp_file.name, xx)
            does_not_exist = path_no_ext+"XXXCCCVVBB"  # Does not end with .bas
            xx = find_program_file(does_not_exist)
            self.assertEqual(does_not_exist, xx)

        print("test_basic passed.")




    # def assert_value(self, executor:Executor, symbol:str, expected_value):
    #     value = executor.get_symbol(symbol)
    #     self.assertEqual(expected_value, value)
    #
    # def assert_values(self, executor:Executor, expected_values):
    #     """
    #     Verifies the symbol table contains the values passed in.
    #     Does NOT check for extra values.
    #     :param executor:
    #     :param expected_values: dict of {var:value}
    #     :return: None. Raises an exception, if needed.
    #     """
    #     for item in expected_values.items():
    #         self.assert_value(executor, item[0], item[1])
    #
    # # TODO These functions are defined in each test file. Need to have a common parent class.
    # def runit(self, listing, trace=False):
    #     program = tokenize(listing)
    #     self.assertEqual(len(listing), len(program))
    #     executor = Executor(program, stack_trace=True)
    #     executor.run_program()
    #     return executor
    #
    # def runit_capture(self, listing):
    #     old = sys.stdout
    #     output = StringIO()
    #     sys.stdout = output
    #     try:
    #         executor = self.runit(listing)
    #     finally:
    #         sys.stdout = old
    #     program_output = output.getvalue()
    #     return executor, program_output
    #
    # def runit_se(self, listing):
    #     """
    #     Run, and verify that the program raises a BasicSyntaxError
    #     :param listing:
    #     :return:
    #     """
    #     with self.assertRaises(BasicSyntaxError):
    #         with mock.patch('sys.stdout', new=StringIO()):
    #             executor = self.runit(listing)

    def test_trace(self):
        # This doesn't actually test the output, but it's handy to have for debugging trace.
        listing = [
            '100 PRINT:PRINT:PRINT:PRINT',
            '110 J=3+2',
            '120 PRINTJ',
        ]
        program = tokenize(listing)
        self.assertEqual(len(listing), len(program))
        with open(TRACE_FILE_NAME, "w") as f:
            executor = Executor(program, trace_file=f)
            with mock.patch('sys.stdout', new=StringIO()):
                executor.run_program()

