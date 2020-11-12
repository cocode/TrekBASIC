from unittest import TestCase
from basic_lexer import Lexer
from basic_operators import OP_MAP, BINOP_MINUS, BINOP_PLUS


class Test(TestCase):

    def test_binops(self):
        stack = []
        lexer = Lexer()
        tokens = lexer.lex('10-7')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = BINOP_MINUS()
        answer = binop.eval(stack)
        self.assertEqual(3, answer.token)

        tokens = lexer.lex('10+7')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = BINOP_PLUS()
        answer = binop.eval(stack)
        self.assertEqual(17, answer.token)

        tokens = lexer.lex('10*7')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = OP_MAP[tokens[1].token].value
        answer = binop.eval(stack)
        self.assertEqual(70, answer.token)

        tokens = lexer.lex('"A " + "B"')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = OP_MAP[tokens[1].token].value
        answer = binop.eval(stack)
        self.assertEqual("A B", answer.token)
