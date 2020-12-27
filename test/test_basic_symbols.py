from unittest import TestCase
from basic_types import SymbolType
from basic_symbols import SymbolTable


class TestSymbolTable(TestCase):

    def test_basic(self):
        sym = SymbolTable()
        sym.put_symbol("A", 3, SymbolType.VARIABLE, arg=None)

        self.assertEqual(1, len(sym))
        value = sym.get_symbol("A")
        self.assertEqual(3, value)
        self.assertEqual(SymbolType.VARIABLE, sym.get_symbol_type("A"))
        self.assertTrue(sym.is_symbol_defined("A"))
        self.assertFalse(sym.is_symbol_defined("B"))

        sym.put_symbol("B", "ABC", SymbolType.VARIABLE, arg=None)
        self.assertEqual(2, len(sym))
        value = sym.get_symbol("B")
        self.assertEqual("ABC", value)

        self.assertEqual(SymbolType.VARIABLE, sym.get_symbol_type("B"))
        self.assertEqual(None, sym.get_symbol_arg("B"))
        self.assertTrue(sym.is_symbol_defined("B"))

        # Check A still works.
        sym_type = sym.get_symbol_type("A")
        self.assertEqual(SymbolType.VARIABLE, sym_type)
        self.assertTrue(sym.is_symbol_defined("A"))

    def test_scope(self):
        outer = SymbolTable()
        inner = outer.get_nested_scope()
        outer.put_symbol("A", 3, SymbolType.VARIABLE, arg=None)
        outer.put_symbol("B", 27, SymbolType.VARIABLE, arg=None)
        self.assertEqual(2, len(inner))
        self.assertEqual(2, len(outer))

        inner.put_symbol("A", "5", SymbolType.VARIABLE, arg="X")
        self.assertEqual(3, len(inner))
        self.assertEqual(2, len(outer))

        # Check the symbol is there on the inner, and it shadows the outer scope.
        self.assertEqual("5", inner.get_symbol("A"))
        self.assertEqual(SymbolType.VARIABLE, inner.get_symbol_type("A"))
        self.assertEqual("X", inner.get_symbol_arg("A"))
        self.assertTrue(inner.is_symbol_defined("A"))

        # Check we can get symbols from outer via inner
        self.assertEqual(27, inner.get_symbol("B"))
        self.assertEqual(SymbolType.VARIABLE, inner.get_symbol_type("B"))
        self.assertEqual(None, inner.get_symbol_arg("B"))
        self.assertTrue(inner.is_symbol_defined("B"))

        # Check outer scope still works.
        self.assertEqual(3, outer.get_symbol("A"))
        self.assertEqual(SymbolType.VARIABLE, outer.get_symbol_type("A"))
        self.assertEqual(None, outer.get_symbol_arg("A"))
        self.assertTrue(outer.is_symbol_defined("A"))

    def test_get_table(self):
        # Note we are checking the length of _symbols here, not the number of symbols.
        s = SymbolTable()
        self.assertEqual(len(s._symbol_tables), 0)
        s.put_symbol("a", "99", SymbolType.VARIABLE, "test")
        self.assertEqual(len(s._symbol_tables), 1)
        s.put_symbol("b", "999", SymbolType.VARIABLE, "test")
        self.assertEqual(len(s._symbol_tables), 1)
        s.put_symbol("b", "9999", SymbolType.ARRAY, "test")
        self.assertEqual(len(s._symbol_tables), 2)
        s.put_symbol("b", "99999", SymbolType.FUNCTION, "test")
        self.assertEqual(len(s._symbol_tables), 3)

    def test_table_types(self):
        """
        The version of BASIC we are emulating has different scopes for ARRAYs and scalar
        variables. Test this.
        :return:
        """
        s = SymbolTable()
        self.assertEqual(len(s), 0)
        s.put_symbol("a", "99", SymbolType.VARIABLE, "test1")
        array = [10]*10
        s.put_symbol("a",[10]*10 , SymbolType.ARRAY, "test2")
        s.put_symbol("a", 'x*x', SymbolType.FUNCTION, "test3")
        self.assertEqual(len(s), 3)
        self.assertEqual("99", s.get_symbol("a", SymbolType.VARIABLE))
        self.assertEqual(array, s.get_symbol("a", SymbolType.ARRAY))
        self.assertEqual("x*x", s.get_symbol("a", SymbolType.FUNCTION))

        outer = s
        inner = s.get_nested_scope()
        # test that all these work when called from an inner scope.
        self.assertEqual(len(inner), 3)
        self.assertEqual("99", inner.get_symbol("a", SymbolType.VARIABLE))
        self.assertEqual(array, inner.get_symbol("a", SymbolType.ARRAY))
        self.assertEqual("x*x", inner.get_symbol("a", SymbolType.FUNCTION))


