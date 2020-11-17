from unittest import TestCase
from basic_types import BasicSyntaxError
from basic_lexer import Lexer


class TestLexer(TestCase):
    def test_lex(self):
        lexer = Lexer()

        tokens = lexer.lex("X1")
        self.assertEqual(1, len(tokens))
        self.assertEqual("id", tokens[0].type)
        self.assertEqual("X1", tokens[0].token)

    def test_lex_builtin(self):
        lexer = Lexer()

        tokens = lexer.lex("RND")
        self.assertEqual(1, len(tokens))
        self.assertEqual("id", tokens[0].type)
        self.assertEqual("RND", tokens[0].token)

        tokens = lexer.lex("D(R1)=D(R1)-H/S-.5*RND(1)")
        expected = [("D", 'id'), ("(", 'op'), ("R1", 'id'), (")", 'op'), ("=", 'op'),
                    ("D", 'id'), ("(", 'op'), ("R1", 'id'), (")", 'op'), ("-", 'op'),
                    ("H", 'id'), ("/", 'op'), ("S", 'id'), ("-", 'op'),
                    (.5, 'num'), ("*", 'op'), ("RND", 'id'), ("(", 'op'), (1, 'num'), (")", 'op')]
        for index, expect in enumerate(expected):
            # print(index, expect)
            self.assertEqual(expect[0], tokens[index].token)
            self.assertEqual(expect[1], tokens[index].type)

        self.assertEqual(len(expected), len(tokens))

    def test_lex_literals(self):
        lexer = Lexer()
        tokens = lexer.lex('"ABC"+"DEF"')
        self.assertEqual(3, len(tokens))
        self.assertEqual("str", tokens[0].type)
        self.assertEqual("ABC", tokens[0].token)
        self.assertEqual("op", tokens[1].type)
        self.assertEqual("+", tokens[1].token)
        self.assertEqual("str", tokens[2].type)
        self.assertEqual("DEF", tokens[2].token)

        with self.assertRaises(BasicSyntaxError):
            lexer.lex('"ABC')

    def test_lex_ne(self):
        lexer = Lexer()
        tokens = lexer.lex("X<>3")
        self.assertEqual(3, len(tokens))
        self.assertEqual("id", tokens[0].type)
        self.assertEqual("X", tokens[0].token)
        self.assertEqual("op", tokens[1].type)
        self.assertEqual("<>", tokens[1].token)
        self.assertEqual("num", tokens[2].type)
        self.assertEqual(3, tokens[2].token)


