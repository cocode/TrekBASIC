from unittest import TestCase
from basic_symbols import SymbolTable


class TestSymbolTable(TestCase):

    def test_basic(self):
        sym = SymbolTable()
        sym.put_symbol("A", 3, "variable", arg=None)
        value = sym.get_symbol("A")
        self.assertEqual(3, value)
        sym_type = sym.get_symbol_type("A")
        self.assertEqual("variable", sym_type)
        self.assertTrue(sym.is_symbol_defined("A"))

        sym.put_symbol("B", "ABC", "variable", arg=None)
        sym_type = sym.get_symbol_type("B")
        self.assertEqual("variable", sym_type)
        self.assertTrue(sym.is_symbol_defined("B"))
        # Check A still works.
        sym_type = sym.get_symbol_type("A")
        self.assertEqual("variable", sym_type)
        self.assertTrue(sym.is_symbol_defined("A"))


