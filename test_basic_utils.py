from io import StringIO
from unittest import TestCase
import sys

from basic_dialect import ARRAY_OFFSET
from basic_statements import Keywords
from basic_utils import smart_split, format_program
from basic_interpreter import Executor, BasicSyntaxError
from basic_statements import is_valid_identifier
from basic_types import SymbolType, ProgramLine, RunStatus
from basic_loading import tokenize_line, load_program, tokenize


class Test(TestCase):

    def test_smart_split(self):
        line = 'PRINT"YOUR MISSION: BEGINS":PRINT"AND ENDS"'
        results = smart_split(line)
        self.assertEqual(2, len(results))
        self.assertEqual('PRINT"YOUR MISSION: BEGINS"', results[0])
        self.assertEqual('PRINT"AND ENDS"', results[1])

        line = "G(8,8),C(9,2),K(3,3),N(3),Z(8,8),D(8)"
        results = smart_split(line,enquote="(", dequote=")", split_char=",")
        self.assertEqual(6, len(results))
        self.assertEqual('G(8,8)', results[0])
        self.assertEqual('C(9,2)', results[1])

