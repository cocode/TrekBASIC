from unittest import TestCase
from basic_types import BasicSyntaxError, lexer_token
from basic_lexer import get_lexer


class TestLexer(TestCase):
    def setUp(self):
        self._lexer = get_lexer()

    def test_lex(self):
        tokens = self._lexer.lex("X1")
        self.assertEqual(1, len(tokens))
        self.assertEqual("id", tokens[0].type)
        self.assertEqual("X1", tokens[0].token)

    def test_lex_builtin(self):
        tokens = self._lexer.lex("RND")
        self.assertEqual(1, len(tokens))
        self.assertEqual("id", tokens[0].type)
        self.assertEqual("RND", tokens[0].token)

    def test_lex_builtin2(self):
        # this is wrong, the lexer handles expressions, not statements. Should not have "D(R1)="
        tokens = self._lexer.lex("D(R1)=D(R1)-H/S-.5*RND(1)")
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
        tokens = self._lexer.lex('"ABC"+"DEF"')
        self.assertEqual(3, len(tokens))
        self.assertEqual("str", tokens[0].type)
        self.assertEqual("ABC", tokens[0].token)
        self.assertEqual("op", tokens[1].type)
        self.assertEqual("+", tokens[1].token)
        self.assertEqual("str", tokens[2].type)
        self.assertEqual("DEF", tokens[2].token)

        with self.assertRaises(BasicSyntaxError):
            self._lexer.lex('"ABC')

    def test_lex_ne(self):
        tokens = self._lexer.lex("X1<>3")
        self.assertEqual(3, len(tokens))
        self.assertEqual("id", tokens[0].type)
        self.assertEqual("X1", tokens[0].token)
        self.assertEqual("op", tokens[1].type)
        self.assertEqual("<>", tokens[1].token)
        self.assertEqual("num", tokens[2].type)
        self.assertEqual(3, tokens[2].token)

    def test_lex_vars(self):
        # Check that we can handle variable names that run into keywords. ("YandQ1then"
        tokens = self._lexer.lex("X<>YANDQ1<7")
        print(tokens)
        expected = [
            lexer_token(token='X', type='id'),
            lexer_token(token='<>', type='op'),
            lexer_token(token='Y', type='id'),
            lexer_token(token='AND', type='op'),
            lexer_token(token='Q1', type='id'),
            lexer_token(token='<', type='op'),
            lexer_token(token=7.0, type='num')
        ]
        self.assertEqual(expected, tokens)




