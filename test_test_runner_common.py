from unittest import TestCase
from trekbasicpy.basic_expressions import Expression
from trekbasicpy.basic_lexer import get_lexer
from trekbasicpy.basic_types import BasicSyntaxError, SymbolType
from trekbasicpy.basic_symbols import SymbolTable
from test_runner_common import get_expected_exit_code_from_text


class Test(TestCase):
    def setUp(self):
        pass

    def test_get_expected_exit_code(self):
        rc = get_expected_exit_code_from_text("100 Rem @EXPECT_EXIT_CODE=2 We want to check the catch and rethrow clause.")
        self.assertEqual(rc, 2)
        rc= get_expected_exit_code_from_text("100 Rem stuff and nonsense. @EXPECT_EXIT_CODE=1.")
        self.assertEqual(rc, 1)
        rc= get_expected_exit_code_from_text("100 Rem stuff and nonsense. EXPECT_EXIT_CODE=1.")
        self.assertEqual(rc, 0)
