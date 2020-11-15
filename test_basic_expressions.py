from unittest import TestCase
from basic_expressions import Expression
from basic_lexer import Lexer
from basic_types import ste, BasicSyntaxError
from basic_interpreter import Executor
from basic_symbols import SymbolTable

class TestExpression(TestCase):
    def setUp(self):
        self._lexer = Lexer()

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
#        entry = ste(22, "variable", None)
        symbol_table = SymbolTable()
        symbol_table.put_symbol("A", 22, "variable", arg=None)
        value = expression.eval(tokens, symbols=symbol_table)
        self.assertEqual(23, value)

    def test_eval8(self):
        tokens = self._lexer.lex('"AB" + A$')
        self.assertEqual(3, len(tokens))
        expression = Expression()
        symbol_table = SymbolTable()
        symbol_table.put_symbol("A$", "C", "variable", arg=None)
        value = expression.eval(tokens, symbols=symbol_table)
        self.assertEqual('ABC', value)

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

    def test_eval_unary_minus9(self):
        tokens = self._lexer.lex("(-7--3)")
        self.assertEqual(7, len(tokens))
        expression = Expression()
        value = expression.eval(tokens)
        self.assertEqual(-4, value)


