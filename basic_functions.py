"""
Definitions for built-in functions.
"""
import random
from math import sin, cos, sqrt, log, exp

import basic_operators as bo


class PredefinedFunctions:
    def __init__(self):
        spaces = bo.StrMonoOp(lambda x: " " * int(x), return_type="str")
        self.functions = {
            "ABS":    bo.MonoOp(lambda x: abs(x)),
            "ASC":    bo.StrMonoOp(lambda x: ord(x), return_type="num"),
            "CHR$":   bo.StrMonoOp(lambda x: chr(int(x)), return_type="str"),
            "COS":    bo.MonoOp(lambda x: cos(x)),
            "EXP":    bo.MonoOp(lambda x: exp(x)),
            "INT":    bo.MonoOp(lambda x: int(x)),
            "LEFT$":  bo.StrOp(lambda x: x[0][:int(x[1])], "LEFT$", 2),
            # This needs to return an int, unlike the other str functions.
            "LEN":    bo.StrOp(lambda x: len(x), "LEN", 1, "num"),
            "LOG":    bo.MonoOp(lambda x: log(x)),
            "MID$":   bo.StrOp(lambda x: x[0][int(x[1]) - 1:int(x[1]) - 1 + int(x[2])], "MID$", 3),
            "RIGHT$": bo.StrOp(lambda x: x[0][-int(x[1]):], "RIGHT$", 2),
            "RND":    bo.MonoOp(lambda x: random.random()),
            "SGN":    bo.MonoOp(lambda x: (x > 0) - (x < 0)),
            "SIN":    bo.MonoOp(lambda x: sin(x)),
            "SQR":    bo.MonoOp(lambda x: sqrt(x)),  # That's Square Root, not Square. At least in this BASIC
            "SPACE$": spaces,  # Sames as TAB function
            "STR$":   bo.StrDollarMonoOp(lambda x: str(x), return_type="str"),
            "TAB":    spaces,
        }

