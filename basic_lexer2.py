"""
Replacement lexer. Not working yet. Keep old one until this is working. May not ever.
Lexical analysis for the basic interpreter. Lexer is currently ONLY used for expressions.

My current thought is that you can't write a context-independent lexer for basic.

IFX>YANDX<ZTHEN100
the lexer only handles the expression "X>YANDX<Z"

I think you have to know that Y is a variable, and can't be longer than one letter. You can't
just grab sequences of letters, like you can in most programming languages. And I don't think
you can know that "IFX" is a keyword and a token with a the lexer, you need to understand the
language.
"""

from basic_types import lexer_token, BasicSyntaxError, NUMBERS, LETTERS
import basic_operators

# It's either a number, an operator, a variable, or other (keyword, function, etc)
OPERATORS = ["(",")","^","*","/","+","-","=",">","<","<>", ">=", "<=", ","]
OP_FIRST = {op[0] for op in OPERATORS}
OP_TWO = [op for op in OPERATORS if len(op) > 1]
OP_TWO_FIRST = {op[0] for op in OP_TWO}
BOOLEAN_OPERATORS=["AND", "OR"] # Strings that have a type of "op"


class Lexer:
    def __init__(self):
        pass

    def scan_for_keyword(self, array, text):
        """
        Find any strings matching an element of array in text.

        :param array:
        :param text:
        :return:
        """
        match = ""
        for i, c in enumerate(text):
            match += c
            potentials = [op for op in array if i < len(op) and op[i] == match[i]]
            #print(c, potentials)

            if not potentials:
                return None
            for p in potentials:
                if i + 1 == len(p):
                    return p
            array = potentials
        return None

    def lex(self, text):
        tokens = [token for token in self.lex2(text)]
        return tokens

    def lex2(self, text):
        state = None
        token = ""
        back = None
        index = 0

        def cur():
            if text is None:
                assert(0)
            if index == len(text):
                return None
            return text[index]

        def peek():
            if index + 1 ==  len(text):
                return None
            return text[index+1]

        def consume():
            nonlocal index
            current = text[index]
            index += 1
            return current # So we can get and consume in one operation.
        ST_ANY = 1
        ST_REF = 2 # VAR, FUNC,
        ST_INT = 3
        ST_FLOAT = 4
        ST_STRING = 5
        state = ST_ANY
        while (c := cur()) is not None:
            print(state, c)
            assert state
            if state == ST_ANY:
                if c == ' ':
                    consume()
                elif c.upper() in LETTERS:
                    token = consume()
                    state = ST_REF
                elif c in NUMBERS:
                    token = consume()
                    state = ST_INT
                elif c == '.': # Number starts with ., like ".5"
                    token = "0"+consume()
                    state = ST_FLOAT
                elif c in OP_FIRST:
                    p = peek()
                    if c not in OP_TWO_FIRST:
                        consume()
                        yield lexer_token(c, "op")
                        state = ST_ANY
                        token = ""
                    elif c+p in OP_TWO:
                        consume()
                        consume()
                        yield lexer_token(c+p, "op")
                        state = ST_ANY
                        token = ""
                    else:
                        consume()
                        yield lexer_token(c, "op")
                        state = ST_ANY
                        token = ""
                elif c =='"':
                    consume()
                    state = ST_STRING
                    token = ""
                else:
                    raise BasicSyntaxError(F"Unexpected char {c} in state {state}")
            elif state == ST_REF:
                if c in NUMBERS: # Need to check for A1$
                    token += consume()
                    yield lexer_token(token, "id")
                    token = ""
                    state = ST_ANY
                elif c.upper() in LETTERS:
                    token += consume()
                else:
                    if token in BOOLEAN_OPERATORS:
                        yield lexer_token(token, "op")
                    else:
                        yield lexer_token(token, "id")
                    token = ""
                    state = ST_ANY
            elif state == ST_INT:
                if c in NUMBERS:
                    token += consume()
                elif c == '.':
                    token += consume()
                    state = ST_FLOAT
                else:
                    yield lexer_token(float(token), "num")
                    token = ""
                    state = ST_ANY
            elif state == ST_FLOAT:
                if c in NUMBERS:
                    token += consume()
                else:
                    yield lexer_token(float(token), "num")
                    token = ""
                    state = ST_ANY
            elif state == ST_STRING:
                if c == '"':
                    consume()
                    yield lexer_token(token, "str")
                    token = ""
                    state = ST_ANY
                else:
                    token += consume()
                    if len(token) > 65536:
                        raise BasicSyntaxError(F"String too long (> 65536).")
            elif c == ' ' or c == '\t':
                consume() # Ignore non quoted whitespace.
            else:
                raise BasicSyntaxError("Invalid character {c} in state {state}")

        # check for tokens in progress
        if state == ST_REF:
            yield lexer_token(token, "id")
        elif state == ST_INT:
            yield lexer_token(int(token), "num")
        elif state == ST_FLOAT:
            yield lexer_token(float(token), "num")
        elif state == ST_STRING:
            raise BasicSyntaxError("END of line in string.")

        return


if __name__ == '__main__':
    p = Lexer()
    tokens = p.lex("XRND")
    # tokens = p.lex("IFX>YANDQ1<7THEN100")
    for t in tokens:
        print("Token: ", t)
    #print(p.consume_from(TEXT_OPERATORS, "AND ABC"))
