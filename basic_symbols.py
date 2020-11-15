"""
This handles the symbol table for the executor
"""
import pprint

from basic_types import ste, assert_syntax


class SymbolTable:
    def __init__(self, scope = None):
        self._symbols = {}
        self._enclosing_scope = scope

    def __len__(self):
        return len(self._symbols)

    def get_copy(self):
        """
        TODO Get rid of this, and use nested scopes
        This must return a copy, not the original, as callers DO make changes for DEF FN
        :return: A new SymbolTable
        """
        new_table = SymbolTable()
        new_table._symbols = self._symbols.copy()
        return new_table

    def get_active_symbols(self):
        """
        This returns the original, and changing it will affect program execution
        :return:
        """
        return self._symbols

    def get_symbol_names(self):
        return self._symbols.keys()

    def put_symbol(self, symbol:str, value, symbol_type:str, arg:str):
        self._symbols[symbol] = ste(value, symbol_type, arg)

    def is_symbol_defined(self, symbol:str):
        """
        :param symbol:
        :return:
        """
        return symbol in self._symbols

    def get_symbol(self, symbol:str):
        """
        :param symbol:
        :return:
        """
        assert_syntax(symbol in self._symbols, F"Variable {symbol} does not exist.")
        return self._symbols[symbol].value

    def get_symbol_type(self, symbol:str):
        """
        :param symbol:
        :return:
        """
        return self._symbols[symbol].type

    def get_symbol_arg(self, symbol:str):
        """
        :param symbol:
        :return:
        """
        return self._symbols[symbol].arg

    def dump(self):
        pprint.pprint(self._symbols)