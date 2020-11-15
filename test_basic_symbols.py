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
        self.assertFalse(sym.is_symbol_defined("B"))

        sym.put_symbol("B", "ABC", "variable", arg=None)
        self.assertEqual("variable", sym.get_symbol_type("B"))
        self.assertEqual(None, sym.get_symbol_arg("B"))
        self.assertTrue(sym.is_symbol_defined("B"))

        # Check A still works.
        sym_type = sym.get_symbol_type("A")
        self.assertEqual("variable", sym_type)
        self.assertTrue(sym.is_symbol_defined("A"))

    def test_scope(self):
        outer = SymbolTable()
        inner = outer.get_nested_scope()
        outer.put_symbol("A", 3, "variable", arg=None)
        outer.put_symbol("B", 27, "variable", arg=None)

        inner.put_symbol("A", "5", "function", arg="X")

        # Check the symbol is there on the inner, and it shadows the outer scope.
        self.assertEqual("5", inner.get_symbol("A"))
        self.assertEqual("function", inner.get_symbol_type("A"))
        self.assertEqual("X", inner.get_symbol_arg("A"))
        self.assertTrue(inner.is_symbol_defined("A"))

        # Check we can get symbols from outer via inner
        self.assertEqual(27, inner.get_symbol("B"))
        self.assertEqual("variable", inner.get_symbol_type("B"))
        self.assertEqual(None, inner.get_symbol_arg("B"))
        self.assertTrue(inner.is_symbol_defined("B"))

        # Check outer scope still works.
        self.assertEqual(3, outer.get_symbol("A"))
        self.assertEqual("variable", outer.get_symbol_type("A"))
        self.assertEqual(None, outer.get_symbol_arg("A"))
        self.assertTrue(outer.is_symbol_defined("A"))






