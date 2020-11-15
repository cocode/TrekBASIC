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

    def get_nested_scope(self):
        """
        Gets a new scope for a user defined function.
        This current SymbolTable (self) will be the outer scope for the new function.

        :return: A new symbol table, that points to the current symbols table as an enclosing scope.
        """
        return SymbolTable(self)

    def get_active_symbols(self):
        """
        This returns the original, and changing it will affect program execution
        :return:
        """
        return self._symbols

    def put_symbol(self, symbol:str, value, symbol_type:str, arg:str):
        self._symbols[symbol] = ste(value, symbol_type, arg)

    def _is_local(self, symbol):
        return symbol in self._symbols

    def is_symbol_defined(self, symbol:str):
        """
        :param symbol:
        :return:
        """
        if self._is_local(symbol):
            return True
        if self._enclosing_scope is not None:
            return self._enclosing_scope.is_symbol_defined(symbol)
        return False

    def get_symbol(self, symbol:str):
        """
        Gets the symbols VALUE. TODO: Rename to get_symbol_value
        :param symbol:
        :return:
        """
        assert_syntax(self.is_symbol_defined(symbol), F"Variable {symbol} does not exist.")
        if self._is_local(symbol):
            return self._symbols[symbol].value
        return self._enclosing_scope.get_symbol(symbol)

    def get_symbol_type(self, symbol:str):
        """
        :param symbol:
        :return:
        """
        assert_syntax(self.is_symbol_defined(symbol), F"Variable {symbol} does not exist.")
        if self._is_local(symbol):
            return self._symbols[symbol].type
        return self._enclosing_scope.get_symbol_type(symbol)

    def get_symbol_arg(self, symbol:str):
        """
        :param symbol:
        :return:
        """
        assert_syntax(self.is_symbol_defined(symbol), F"Variable {symbol} does not exist.")
        if self._is_local(symbol):
            return self._symbols[symbol].arg
        return self._enclosing_scope.get_symbol_arg(symbol)

    def dump(self):
        pprint.pprint(self._symbols)