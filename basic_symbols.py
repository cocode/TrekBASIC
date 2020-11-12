"""
This handles the symbol table for the executor
"""

from basic_types import ste


class SymbolTable:
    def __init__(self):
        self._symbols = {}

    def __len__(self):
        return len(self._symbols)

    def get_copy(self):
        """
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

    def get_symbol(self, symbol:str):
        """
        :param symbol:
        :return:
        """
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
