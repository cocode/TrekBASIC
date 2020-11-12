from unittest import TestCase
from basic_expressions import Expression
from basic_lexer import Lexer
from basic_types import ste

class TestExpression(TestCase):
    def test_eval(self):
        lexer = Lexer()

        tokens = lexer.lex("1")
        self.assertEqual(1, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual(1, value)

        tokens = lexer.lex("ABC")
        self.assertEqual(1, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual("ABC", value)

        tokens = lexer.lex("1-3")
        self.assertEqual(3, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual(-2.0, value)

        tokens = lexer.lex("1-3*2")
        self.assertEqual(5, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual(-5.0, value)

        tokens = lexer.lex(" 1 - 3 * 2 ")
        self.assertEqual(5, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual(-5.0, value)

        tokens = lexer.lex(" 1 + 2 * 3 ^ 4 - 3")
        self.assertEqual(9, len(tokens))
        expression = Expression()
        value = expression.eval(None, tokens, 0)
        self.assertEqual(160, value)

        tokens = lexer.lex(" 1 + A")
        self.assertEqual(3, len(tokens))
        expression = Expression()
        entry = ste(22, "variable")
        value = expression.eval({"A":entry}, tokens, 0)
        self.assertEqual(23, value)

        tokens = lexer.lex('"AB" + A$')
        self.assertEqual(3, len(tokens))
        expression = Expression()
        entry = ste("C", "variable")
        value = expression.eval({"A$":entry}, tokens, 0)
        self.assertEqual('ABC', value)
