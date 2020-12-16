"""
Experiments with state machines. Not doing anything meaningful yet.
"""
from itertools import count
from collections import defaultdict

from basic_utils import smart_split

grammar = ["abc", "abd", "def"]
#
# sb = {
#     "a": {
#         "b": {
#             "c": {
#
#             },
#             "d": {
#
#             }
#
#         }
#     },
#     "b": {
#
#     },
# }



class State:
    _next_id = count(0)

    def __init__(self):
        self.id = next(State._next_id)
        self._transitions = {}

    def extend(self, strings):
        for s in strings:
            self.add(s)

    def add(self, input):
        assert len(input) > 0 # Not sure what to do if ""
        first = input[0]
        remainder = input[1:]

        if first in self._transitions:
            state =  self._transitions[first]
        else:
            state = State()
            self._transitions[first] = state
        if len(remainder) > 0:
            state.add(remainder)

    def match(self, input):
        if len(input) == 0:
            if len(self._transitions) == 0:
                return True
            return False

        first = input[0]
        remainder = input[1:]

        if first in self._transitions:
            next_state = self._transitions[first]
            return next_state.match(remainder)
        return False


    def next(self, input):
        return self._transitions[input]

    def __str__(self):
        return F"(State): {self.id}:{self._transitions}"

    def __repr__(self):
        return self.__str__()


def parse_ebnf(ebnf:str) -> State:
    """
    Convet an EBNF description string to a Python data structure.

    Using this EBNF (there are many variants) https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form

    :param ebnf:
    :return:
    """
    rules = smart_split(ebnf, split_char=";")
    r = {}
    for rule in rules:
        rule = rule.strip()
        if not rule:
            continue
        lhs, rhs = rule.split('=', 1)
        rhs = smart_split(rhs, split_char="|")
        rhs = [r.strip() for r in rhs]
        state = State()
        state.extend(rhs)
        r[lhs.strip()] = state
    return r


def print_state(state, indent=""):
    # print(F"{indent}{state.id}: {{")
    print(F"{{")
    for key in state._transitions:
        print(F"{indent}\t{key} => ", end='')
        print_state(state._transitions[key], indent = indent+"    ")
    print(F"{indent}}}")

if __name__ == "__main__":
    start_state = State()
    assert start_state.match("")

    # Test that it can handle one string.
    start_state.add("abc")
    assert start_state.match("abc")

    start_state.add("abd")

#    build_tree(start_state, grammar.copy())
    import pprint
    pprint.pprint(start_state, indent=4)
    assert start_state.match("abd")

    start_state.add("bcd")
    assert start_state.match("abc")
    assert start_state.match("abd")
    assert start_state.match("bcd")
    assert not start_state.match("bcde")
    assert not start_state.match("def")

    print_state(start_state)
    grammar = """
    first = abc | abd | bcd;
    """
    print("=====================================")
    rules = parse_ebnf(grammar)
    for r in rules:
        print("rule: ", r, " ::= ")
        print_state(rules[r])

    sm = rules['first']

    assert start_state.match("abc")
    assert start_state.match("abd")
    assert start_state.match("bcd")
    assert not start_state.match("bcde")
    assert not start_state.match("def")

