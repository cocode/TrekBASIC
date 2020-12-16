"""
Experiments with state machines. Not doing anything meaningful yet.
"""
from itertools import count
from collections import defaultdict

grammar = ["abc", "abd", "def"]

sb = {
    "a": {
        "b": {
            "c": {

            },
            "d": {
                
            }

        }
    },
    "b": {

    },
}

state_list = []


class State:
    _next_id = count(0)

    def __init__(self):
        self.id = next(State._next_id)
        self._transitions = {}

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


def build_tree(state, grammar):
    """
    Given a grammar, build a state machine that recognizes it.

    Given a set of strings, find unique first characters.

    :param state:
    :param gc:
    :return:
    """
    tree = {}
    # Generate a list of inputs, and the "grammar" for the next state
    for i in range(0, len(grammar)):
        print(i)
        cur = grammar[i]
        # Current input
        char = cur[0]
        # Remaining part of input.
        gr1 = cur[1:]
        # Accumulate list of all strings that started with char.
        if char in tree:
            gr = tree.get(char)
            gr.append(gr1)
        else:
            tree[char] = [gr1]

    # for input in tree:
    #     state
    #     state.


def print_state(state, indent=""):
    print(F"{indent}State: {state.id} indent ='{indent}'")
    for key in state._transitions:
        print(F"{indent}\t{key}")
        print_state(state._transitions[key], indent = indent+"    ")

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



