
import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import builtins

from trekbasicpy import basic
from trekbasicpy.basic_types import RunStatus, BasicSyntaxError


class TestBasicModuleCoverage(unittest.TestCase):

    def test_execute_program_runtime_error(self):
        program = MagicMock()
        executor = MagicMock()
        executor.run_program.side_effect = BasicSyntaxError("error", 42)
        with patch("trekbasicpy.basic.Executor", return_value=executor),              patch("builtins.print") as mock_print:
            run_status, returned_executor = basic.execute_program(program)
        self.assertEqual(run_status, RunStatus.END_ERROR_SYNTAX)
        self.assertEqual(returned_executor, executor)
        mock_print.assert_called_with("error in line 42 of file.")

    def test_execute_program_with_timing(self):
        program = MagicMock()
        executor = MagicMock()
        executor.run_program.return_value = RunStatus.END_OF_PROGRAM
        with patch("trekbasicpy.basic.Executor", return_value=executor),              patch("time.time", side_effect=[1.0, 2.5]),              patch("builtins.print") as mock_print:
            result, _ = basic.execute_program(program, enable_timing=True)
        self.assertEqual(result, RunStatus.END_OF_PROGRAM)
        mock_print.assert_called_with("Execution time: 1.50000 seconds")

    def test_dump_symbol_table(self):
        executor = MagicMock()
        executor._symbols.dump.return_value = {"A": 1}
        with patch("pprint.pprint") as mock_pprint:
            basic.dump_symbol_table(executor)
        mock_pprint.assert_called_once_with({"A": 1})

    def test_determine_exit_code(self):
        self.assertEqual(basic.determine_exit_code(RunStatus.END_OF_PROGRAM), 0)
        self.assertEqual(basic.determine_exit_code(RunStatus.END_CMD), 0)
        self.assertEqual(basic.determine_exit_code(RunStatus.END_STOP), 1)
        # TODO: These should be 2 and 3, not 2 and 2.  Change that at some point.
        self.assertEqual(basic.determine_exit_code(RunStatus.END_ERROR_RUNTIME), 3)
        self.assertEqual(basic.determine_exit_code(RunStatus.END_ERROR_SYNTAX), 2)


if __name__ == "__main__":
    unittest.main()
