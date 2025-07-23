from trekbasicpy.basic_types import BasicSyntaxError, LETTERS, NUMBERS, lexer_token
import trekbasicpy.basic_functions

# Symbolic operators
OPERATORS = {"(", ")", "^", "*", "/", "+", "-", "=", ">", "<", ",", "#"}

# Text operators (must be surrounded by whitespace or token boundaries)
BOOLEAN_OPERATORS = ["AND", "OR", "MOD"]

functions = trekbasicpy.basic_functions.PredefinedFunctions()
BUILT_IN_FUNCTIONS = sorted([key.upper() for key in functions.functions])

RESERVED_WORDS = set(BOOLEAN_OPERATORS + BUILT_IN_FUNCTIONS)

# Type suffixes allowed at end of identifier
TYPE_SUFFIXES = {"$", "%", "!", "#"}


class LexerModernLongVar:
    def __init__(self):
        pass

    def lex(self, text):
        return list(self.lex2(text))

    def lex2(self, text):
        index = 0
        length = len(text)

        def cur():
            return text[index] if index < length else None

        def peek():
            return text[index + 1] if index + 1 < length else None

        def consume():
            nonlocal index
            c = text[index]
            index += 1
            return c

        def consume_while(pred):
            result = ''
            while (c := cur()) is not None and pred(c):
                result += consume()
            return result

        def skip_whitespace():
            nonlocal index
            while cur() in {' ', '\t'}:
                consume()

        while (c := cur()) is not None:
            if c in {' ', '\t'}:
                skip_whitespace()
                continue

            if c == '\n':
                break

            if c.upper() in LETTERS:
                identifier = consume()

                while (cur() is not None and
                       (cur().upper() in LETTERS or cur() in NUMBERS or cur() == ".")):
                    identifier += consume()

                if cur() in TYPE_SUFFIXES:
                    identifier += consume()

                identifier_upper = identifier.upper()
                truncated = identifier_upper[:40]

                # Boolean operators only allowed when clearly separated
                if truncated in BOOLEAN_OPERATORS:
                    yield lexer_token(truncated, "op")
                elif truncated in BUILT_IN_FUNCTIONS:
                    yield lexer_token(truncated, "id")
                else:
                    if truncated in BOOLEAN_OPERATORS:
                        raise BasicSyntaxError(f"'{identifier}' must be separated by space.")
                    yield lexer_token(truncated, "id")

            elif c in OPERATORS:
                op = consume()
                nxt = cur()
                combined = None

                if op == "<" and nxt == ">":
                    consume()
                    combined = "<>"
                elif op == "<" and nxt == "=":
                    consume()
                    combined = "<="
                elif op == ">" and nxt == "=":
                    consume()
                    combined = ">="

                yield lexer_token(combined if combined else op, "op")

            elif c in NUMBERS or c == ".":
                number = consume_while(lambda ch: ch in NUMBERS or ch == ".")
                try:
                    yield lexer_token(float(number), "num")
                except ValueError:
                    raise BasicSyntaxError(f"Invalid number literal: {number}")

            elif c == '"':
                consume()
                string_value = ""
                while cur() not in {None, '"'}:
                    string_value += consume()
                if cur() != '"':
                    raise BasicSyntaxError("Unclosed string literal.")
                consume()
                yield lexer_token(string_value, "str")

            else:
                raise BasicSyntaxError(f"Unexpected character '{c}'")
