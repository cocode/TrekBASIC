from unittest import TestCase
from trekbasicpy.basic_types import BasicSyntaxError, lexer_token
from trekbasicpy.basic_lexer_long_var import LexerModernLongVar  # Direct import of the modern lexer

class TestLongVarLexer(TestCase):
    def setUp(self):
        self._lexer = LexerModernLongVar()

    def test_simple_variable(self):
        tokens = self._lexer.lex("X1")
        self.assertEqual([lexer_token("X1", "id")], tokens)

    def test_builtin_function(self):
        tokens = self._lexer.lex("RND")
        self.assertEqual([lexer_token("RND", "id")], tokens)

    def test_function_call_and_expression(self):
        tokens = self._lexer.lex("DEF FNred%(A) + LIMIT! / X1 + FNLOG(ARR(3))")
        expected = [
            lexer_token("DEF", "id"),
            lexer_token("FNRED%", "id"),
            lexer_token("(", "op"),
            lexer_token("A", "id"),
            lexer_token(")", "op"),
            lexer_token("+", "op"),
            lexer_token("LIMIT!", "id"),
            lexer_token("/", "op"),
            lexer_token("X1", "id"),
            lexer_token("+", "op"),
            lexer_token("FNLOG", "id"),
            lexer_token("(", "op"),
            lexer_token("ARR", "id"),
            lexer_token("(", "op"),
            lexer_token(3.0, "num"),
            lexer_token(")", "op"),
            lexer_token(")", "op"),
        ]
        self.assertEqual(expected, tokens)

    def test_string_literals(self):
        tokens = self._lexer.lex('"ABC"+"DEF"')
        expected = [
            lexer_token("ABC", "str"),
            lexer_token("+", "op"),
            lexer_token("DEF", "str")
        ]
        self.assertEqual(expected, tokens)

        with self.assertRaises(BasicSyntaxError):
            self._lexer.lex('"ABC')

    def test_not_equal_operator(self):
        tokens = self._lexer.lex("X1<>3")
        expected = [
            lexer_token("X1", "id"),
            lexer_token("<>", "op"),
            lexer_token(3.0, "num")
        ]
        self.assertEqual(expected, tokens)

    def test_vars_near_keywords(self):
        # No space between Y and AND — treated as a single identifier
        tokens = self._lexer.lex("X<>YANDQ1<7")
        expected = [
            lexer_token("X", "id"),
            lexer_token("<>", "op"),
            lexer_token("YANDQ1", "id"),
            lexer_token("<", "op"),
            lexer_token(7.0, "num")
        ]
        self.assertEqual(expected, tokens)
