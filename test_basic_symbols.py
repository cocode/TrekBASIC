from unittest import TestCase
from basic_symbols import SymbolTable


class TestSymbolTable(TestCase):

    def test_basic(self):
        sym = SymbolTable()
        sym.put_symbol("A", 3, "variable", arg=None)
        value = sym.get_symbol("A")
        self.assertEqual(3, value)
        self.assertTrue(sym.is_symbol_defined("A"))


