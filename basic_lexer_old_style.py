"""
Lexical analysis for the basic intepreter. *** Lexer is ONLY used for expressions. ***

My current thought is that you can't write a context-independent lexer for basic.

IF X>YANDX<ZTHEN100

I think you have to know that Y is a variable, and can't be longer than one letter, you can't
just grab sequences of letters.
"""
from basic_types import lexer_token, BasicSyntaxError, NUMBERS, LETTERS
import basic_functions

OPERATORS = "()^*/+-=><,#"
BOOLEAN_OPERATORS=["AND", "OR"]


functions = basic_functions.PredefinedFunctions()
BUILT_IN_FUNCTIONS=sorted([ key for key in functions.functions])
FN_OPERATORS=["FN"+chr(c) for c in range(ord("A"), ord("Z"))]
# Operators made from letters, not symbols.
TEXT_OPERATORS=BOOLEAN_OPERATORS + BUILT_IN_FUNCTIONS + FN_OPERATORS


class LexerOldStyle:
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
            if index +1 ==  len(text):
                return None
            return text[index+1]

        def consume():
            nonlocal index
            current = text[index]
            index += 1
            return current # So we can get and consume in one operation.

        while (c := cur()) is not None:
            if state is None:
                if c.upper() in LETTERS:
                    token = ""
                    if peek() is not None and peek() in NUMBERS or peek() == '$':
                        # Only consume if on identifier path.
                        token += consume().upper()
                        if cur() in NUMBERS:
                            token += consume()
                        if cur() == '$':
                            token += consume()
                        yield lexer_token(token, "id")
                        continue

                    if peek() is None or peek().upper() not in LETTERS:
                        yield lexer_token(consume(), "id")
                        continue

                    # At this point, we know it's not a variable.
                    found = self.scan_for_keyword(TEXT_OPERATORS, text[index:].upper())
                    if not found:
                        # Can't make an operator from it, so much be an ID.
                        yield lexer_token(consume(), "id")
                        continue

                    for _ in found:
                        consume()
                    if found in BOOLEAN_OPERATORS:
                        yield lexer_token(found, "op")
                    else:
                        yield lexer_token(found, "id")
                elif c in OPERATORS:
                    first = consume()
                    if first == "<" and cur() == ">":
                        consume()
                        yield lexer_token("<>", "op")
                    elif first == "<" and cur() == "=":
                        consume()
                        yield lexer_token("<=", "op")
                    elif first == ">" and cur() == "=":
                        consume()
                        yield lexer_token(">=", "op")
                    else:
                        yield lexer_token(first, "op")
                elif c in NUMBERS or c == '.':
                    token = ""
                    while (c := cur()) is not None and (c in NUMBERS or c == '.'):
                        token += consume()
                    yield lexer_token(float(token), "num")
                elif c == '"':
                    consume()
                    token = ""
                    while (c := cur()) is not None and (c != '"'):
                        token += consume()
                    if cur() != '"':
                        raise BasicSyntaxError(F"No closing quote char.")
                    consume()
                    yield lexer_token(token, "str")
                elif c == ' ' or c == '\t':
                    consume() # Ignore non quoted whitespace.
                else:
                    raise BasicSyntaxError(F"Unexpected char '{c}'")

        return


if __name__ == '__main__':
    p = Lexer()
    tokens = p.lex("XRND")
    # tokens = p.lex("IFX>YANDQ1<7")
    for t in tokens:
        print("Token: ", t)
    #print(p.consume_from(TEXT_OPERATORS, "AND ABC"))
