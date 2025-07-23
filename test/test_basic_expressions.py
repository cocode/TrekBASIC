from unittest import TestCase
from trekbasicpy.basic_expressions import Expression
from trekbasicpy.basic_lexer import get_lexer
from trekbasicpy.basic_types import BasicSyntaxError, SymbolType
from trekbasicpy.basic_symbols import SymbolTable


class Test(TestCase):
    def setUp(self):
        self._lexer = get_lexer()

    def test_eval1(self):
        tokens = self._lexer.lex("1")
        self.assertEqual(1, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(1, value)

    def test_eval2(self):
        tokens = self._lexer.lex('"ABC"')
        self.assertEqual(1, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual("ABC", value)

    def test_eval3(self):
        tokens = self._lexer.lex("1-3")
        self.assertEqual(3, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(-2.0, value)

    def test_eval4(self):
        tokens = self._lexer.lex("1-3*2")
        self.assertEqual(5, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(-5.0, value)

    def test_eval5(self):
        tokens = self._lexer.lex(" 1 - 3 * 2 ")
        self.assertEqual(5, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(-5.0, value)

    def test_eval6(self):
        tokens = self._lexer.lex(" 1 + 2 * 3 ^ 4 - 3")
        self.assertEqual(9, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(160, value)

    def test_eval7(self):
        tokens = self._lexer.lex(" 1 + A")
        self.assertEqual(3, len(tokens))
        expression = Expression()
        symbol_table = SymbolTable()
        symbol_table.put_symbol("A", 22, SymbolType.VARIABLE, arg=None)
        value = expression.eval(tokens, symbols=symbol_table)
        self.assertEqual(23, value)

    def test_eval8(self):
        tokens = self._lexer.lex('"AB" + A$')
        self.assertEqual(3, len(tokens))
        expression = Expression()
        symbol_table = SymbolTable()
        symbol_table.put_symbol("A$", "C", SymbolType.VARIABLE, arg=None)
        value = expression.eval(tokens, symbols=symbol_table)
        self.assertEqual('ABC', value)

    def test_eval9(self):
        # Currently, our basic is LEFT associative for everything. That seems to have been common
        # for BASICs, but seems to not be the mathematical standard.
        tokens = self._lexer.lex('2^3^2')
        self.assertEqual(5, len(tokens))
        expression = Expression()
        symbol_table = SymbolTable()
        value = expression.eval(tokens, symbols=symbol_table)
        self.assertEqual(64, value)

    def test_eval_parens1(self):
        tokens = self._lexer.lex("(7-3)")
        self.assertEqual(5, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(4, value)

    def test_eval_parens2(self):
        tokens = self._lexer.lex("(7-3) * 2")
        self.assertEqual(7, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(8, value)

    def test_eval_parens3(self):
        tokens = self._lexer.lex(" 1 +(7-3) * 2")
        self.assertEqual(9, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(9, value)

    def test_eval_parens4(self):
        tokens = self._lexer.lex("(7-3) * (2*4) - (2+5)")
        self.assertEqual(17, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(25, value)

    def test_eval_parens5(self):
        tokens = self._lexer.lex("(7-3) * ((2*4) - (2+5))")
        self.assertEqual(19, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(4, value)

    def test_eval_unary_minus1(self):
        tokens = self._lexer.lex("-9")
        self.assertEqual(2, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(-9, value)

    def test_eval_unary_minus2(self):
        tokens = self._lexer.lex("-9*3")
        self.assertEqual(4, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(-27, value)

    def test_eval_unary_minus3(self):
        tokens = self._lexer.lex("10*-8")
        self.assertEqual(4, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(-80, value)

    def test_eval_unary_minus4(self):
        tokens = self._lexer.lex("-(8+3)")
        self.assertEqual(6, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(-11, value)

    def test_eval_unary_minus5(self):
        tokens = self._lexer.lex("-(2+3)*-(4+5)+-1")
        self.assertEqual(16, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(44, value)

    def test_eval_unary_minus6(self):
        tokens = self._lexer.lex("--9")
        self.assertEqual(3, len(tokens))
        expression = Expression()
        with self.assertRaises(BasicSyntaxError):
            value = expression.eval(tokens)

    def test_eval_unary_minus7(self):
        tokens = self._lexer.lex("(2+3)-1")
        self.assertEqual(7, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(4, value)

    def test_eval_unary_minus8(self):
        tokens = self._lexer.lex("(7-3)")
        self.assertEqual(5, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(4, value)

    def test_eval_unary_minus9(self):
        tokens = self._lexer.lex("(-7-3)")
        self.assertEqual(6, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(-10, value)

    def test_eval_unary_minus10(self):
        tokens = self._lexer.lex("(-7--3)")
        self.assertEqual(7, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(-4, value)

    def test_comma(self):
        tokens = self._lexer.lex('(1,2)')
        self.assertEqual(5, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual([1,2], value)

        tokens = self._lexer.lex('(1,2,3,4,5)')
        self.assertEqual(11, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual([1,2,3,4,5], value)

        tokens = self._lexer.lex('(1,2),(3,4)')
        self.assertEqual(11, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual([1, 2, 3, 4], value)

    def test_types_x(self):
        tokens = self._lexer.lex('"a" + "b" + "c"')
        self.assertEqual(5, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual("abc", value)

    def test_example_x(self):
        tokens = self._lexer.lex('E>10 OR D(7)=0')
        self.assertEqual(10, len(tokens))
        s = SymbolTable()
        s.put_symbol("E", 3000, SymbolType.VARIABLE, None)
        s.put_symbol("D", [0,0,0,0, 0,0,0,0], SymbolType.ARRAY, None)
        expression = Expression()
        value = expression.eval(tokens, symbols=s)
        self.assertEqual(True, value)

    def test_example_x2(self):
        tokens = self._lexer.lex('E>10ORD(7)=0')
        self.assertEqual(10, len(tokens))
        s = SymbolTable()
        s.put_symbol("E", 3000, SymbolType.VARIABLE, None)
        s.put_symbol("D", [0,0,0,0, 0,0,0,0], SymbolType.ARRAY, None)
        expression = Expression()
        value = expression.eval(tokens, symbols=s)
        self.assertEqual(True, value)

    def test_get_type_from_name(self):
        expression = Expression()
        tokens = self._lexer.lex('A$')
        self.assertEqual(SymbolType.VARIABLE, expression.get_type_from_name(tokens[0], tokens, 0))
        tokens = self._lexer.lex('A$')
        self.assertEqual(SymbolType.VARIABLE, expression.get_type_from_name(tokens[0], tokens, 0))
        tokens = self._lexer.lex('A1$')
        self.assertEqual(SymbolType.VARIABLE, expression.get_type_from_name(tokens[0], tokens, 0))
        tokens = self._lexer.lex('STR$')
        self.assertEqual(SymbolType.FUNCTION, expression.get_type_from_name(tokens[0], tokens, 0))
        tokens = self._lexer.lex('A(')
        self.assertEqual(SymbolType.ARRAY, expression.get_type_from_name(tokens[0], tokens, 0))


    def test_tuples(self):
        expression = Expression()
        tokens = self._lexer.lex('1,2')
        self.assertEqual(3, len(tokens))
        expression = Expression()
        s = SymbolTable()
        value = expression.eval(tokens, symbols=s)
        self.assertEqual([1.0, 2.0], value)

    def test_abs(self):
        tokens = self._lexer.lex("ABS(-3-4)")
        self.assertEqual(7, len(tokens))
        expression = Expression()
        s = SymbolTable()
        s.put_symbol("ABS", "⌊", SymbolType.FUNCTION, arg=None)
        value = expression.eval(tokens, symbols=s)
        self.assertEqual(7, value)
