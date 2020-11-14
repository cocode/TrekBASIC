from unittest import TestCase
from basic_types import BasicSyntaxError
from basic_lexer import Lexer, lexer_token


class TestLexer(TestCase):
    def test_lex(self):
        lexer = Lexer()

        tokens = lexer.lex("X")
        self.assertEqual(1, len(tokens))
        self.assertEqual("id", tokens[0].type)
        self.assertEqual("X", tokens[0].token)

        tokens = lexer.lex("D(R1)=D(R1)-H/S-.5*RND(1)")
        self.assertEqual(20, len(tokens))
        self.assertEqual("id", tokens[0].type)
        self.assertEqual("D", tokens[0].token)
        self.assertEqual("op", tokens[9].type)
        self.assertEqual("-", tokens[9].token)
        self.assertEqual("num", tokens[14].type)
        self.assertEqual(.5, tokens[14].token)
        self.assertEqual("id", tokens[16].type)
        self.assertEqual("RND", tokens[16].token)

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



