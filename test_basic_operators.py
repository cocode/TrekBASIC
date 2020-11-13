from unittest import TestCase
from basic_lexer import Lexer
from basic_operators import get_op, BINOP_MINUS, BINOP_PLUS, MINUS_MONO_OP


class Test(TestCase):
    def setUp(self):
        # Just use the lexer for convenience. We culd just create the tokens used for operands manually
        self._lexer = Lexer()

    def test_minus(self):
        stack = []
        tokens = self._lexer.lex('10-7')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = BINOP_MINUS()
        answer = binop.eval(stack, op=None) # Op is not needed for this test. Only used for DEF FNx
        self.assertEqual(3, answer.token)

    def test_plus(self):
        stack = []
        tokens = self._lexer.lex('10+7')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = BINOP_PLUS()
        answer = binop.eval(stack, op=None)
        self.assertEqual(17, answer.token)

    def test_spaces(self):
        stack = []
        tokens = self._lexer.lex(' 10 + 7 ')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = BINOP_PLUS()
        answer = binop.eval(stack, op=None)
        self.assertEqual(17, answer.token)

    def test_mul(self):
        stack = []
        tokens = self._lexer.lex('10*7')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = get_op(tokens[1], line=0).value
        answer = binop.eval(stack, op=None)
        self.assertEqual(70, answer.token)

    def test_div(self):
        stack = []
        tokens = self._lexer.lex('10/5')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = get_op(tokens[1], line=0).value
        answer = binop.eval(stack, op=None)
        self.assertEqual(2, answer.token)

        tokens = self._lexer.lex('12/5')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = get_op(tokens[1], line=0).value
        answer = binop.eval(stack, op=None)
        self.assertEqual(2.4, answer.token)

    def test_exp(self):
        stack = []
        tokens = self._lexer.lex('2^3')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = get_op(tokens[1], line=0).value
        answer = binop.eval(stack, op=None)
        self.assertEqual(8, answer.token)


    def test_string_concat(self):
        stack = []
        tokens = self._lexer.lex('"A " + "B"')
        self.assertEqual(3, len(tokens))
        stack.append(tokens[0])
        stack.append(tokens[2])
        binop = get_op(tokens[1], line=0).value
        answer = binop.eval(stack, op=None)
        self.assertEqual("A B", answer.token)

    def test_unary_minus(self):
        stack = []
        tokens = self._lexer.lex('3.14')
        self.assertEqual(1, len(tokens))
        stack.append(tokens[0])
        # The lexer doesn't know the difference between unary minus and subtraction.
        # That comes from context, which the expression evaluation has.
        minus = MINUS_MONO_OP()
        answer = minus.eval(stack, op=None)
        self.assertEqual(-3.14, answer.token)
