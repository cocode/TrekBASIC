from unittest import TestCase
from basic_expressions import Expression
from basic_lexer import Lexer
from basic_types import ste

class TestExpression(TestCase):
    def setUp(self):
        self._lexer = Lexer()

    def test_eval1(self):
        tokens = self._lexer.lex("1")
        self.assertEqual(1, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual(1, value)

    def test_eval2(self):
        tokens = self._lexer.lex("ABC")
        self.assertEqual(1, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual("ABC", value)

    def test_eval3(self):
        tokens = self._lexer.lex("1-3")
        self.assertEqual(3, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual(-2.0, value)

    def test_eval4(self):
        tokens = self._lexer.lex("1-3*2")
        self.assertEqual(5, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual(-5.0, value)

    def test_evel5(self):
        tokens = self._lexer.lex(" 1 - 3 * 2 ")
        self.assertEqual(5, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual(-5.0, value)

    def test_evel6(self):
        tokens = self._lexer.lex(" 1 + 2 * 3 ^ 4 - 3")
        self.assertEqual(9, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual(160, value)

    def test_evel7(self):
        tokens = self._lexer.lex(" 1 + A")
        self.assertEqual(3, len(tokens))
        expression = Expression()
        entry = ste(22, "variable", None)
        value = expression.eval({"A":entry}, tokens, 0)
        self.assertEqual(23, value)

    def test_evel8(self):
        tokens = self._lexer.lex('"AB" + A$')
        self.assertEqual(3, len(tokens))
        expression = Expression()
        entry = ste("C", "variable", None)
        value = expression.eval({"A$":entry}, tokens, 0)
        self.assertEqual('ABC', value)

    def test_eval_parens1(self):
        tokens = self._lexer.lex("(7-3)")
        self.assertEqual(5, len(tokens))
        expression = Expression()
        value = expression.eval({}, tokens, 0)
        self.assertEqual(4, value)

    def test_eval_parens2(self):
        tokens = self._lexer.lex("(7-3) * 2")
        self.assertEqual(7, len(tokens))
        expression = Expression()
        value = expression.eval({}, tokens, 0)
        self.assertEqual(8, value)

    def test_eval_parens3(self):
        tokens = self._lexer.lex(" 1 +(7-3) * 2")
        self.assertEqual(9, len(tokens))
        expression = Expression()
        value = expression.eval({}, tokens, 0)
        self.assertEqual(9, value)

    def test_eval_parens4(self):
        tokens = self._lexer.lex("(7-3) * (2*4) - (2+5)")
        self.assertEqual(17, len(tokens))
        expression = Expression()
        value = expression.eval({}, tokens, 0)
        self.assertEqual(25, value)

    def test_eval_parens5(self):
        tokens = self._lexer.lex("(7-3) * ((2*4) - (2+5))")
        self.assertEqual(19, len(tokens))
        expression = Expression()
        value = expression.eval({}, tokens, 0)
        self.assertEqual(4, value)
