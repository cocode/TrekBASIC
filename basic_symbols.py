"""
This handles the symbol table for the executor
"""
import pprint

from basic_types import ste, assert_syntax, SymbolType, UndefinedSymbol


class SymbolTable:
    def __init__(self, scope = None):
        self._symbol_tables = {}
        # Enclosing scopes are used to make local scopes for user defined functions.
        self._enclosing_scope = scope

    def local_length(self):
        """
        Gets the total number of symbols in all tables, but not including enclosing scopes.
        :return:
        """
        length = 0
        for entry in self._symbol_tables.items():
            length += len(entry[1])
        return length

    def __len__(self):
        """
        Gets the total number of symbols in all tables, including enclosing scopes.
        :return:
        """
        length = self.local_length()
        if self._enclosing_scope:
            length += len(self._enclosing_scope)
        return length

    def get_nested_scope(self):
        """
        Gets a new scope for a user defined function.
        This current SymbolTable (self) will be the outer scope for the new function.

        A symbol is first returned from the inner scope. If it is not found in the inner scope,
        the outer (enclosing) scope is returned.

        :return: A new symbol table, that points to the current symbols table as an enclosing scope.
        """
        return SymbolTable(self)

    def get_table(self, symbol_type):
        if symbol_type in self._symbol_tables:
            return self._symbol_tables[symbol_type]

        symbol_table = {}
        self._symbol_tables[symbol_type] = symbol_table
        return symbol_table

    def put_symbol(self, symbol:str, value, symbol_type:SymbolType, arg:str):
        assert SymbolType == type(symbol_type)
        symbol_table = self.get_table(symbol_type)
        symbol_table[symbol] = ste(value, symbol_type, arg)

    def _is_local(self, symbol, symbol_type:SymbolType):
        symbol_table = self.get_table(symbol_type)
        return symbol in symbol_table

    def is_symbol_defined(self, symbol:str, symbol_type:SymbolType=SymbolType.VARIABLE):
        """
        :param symbol:
        :return:
        """
        if self._is_local(symbol, symbol_type):
            return True
        if self._enclosing_scope is not None:
            return self._enclosing_scope.is_symbol_defined(symbol, symbol_type)
        return False

    def _get_symbol_entry(self, symbol:str, symbol_type:SymbolType=SymbolType.VARIABLE)-> ste:
        """
        Gets the symbols entry in the symbol table
        :param symbol: The name of the symbol
        :param symbol_type: The type of the symbol
        :return: The Symbol Table Entry for this variable.
        """
        # TODO We are looking this up three times.
        if not self.is_symbol_defined(symbol, symbol_type):
            raise UndefinedSymbol(F"Variable {symbol} does not exist.")

        symbol_table = self.get_table(symbol_type)
        if self._is_local(symbol, symbol_type):
            return symbol_table[symbol]
        return self._enclosing_scope._get_symbol_entry(symbol, symbol_type)

    def get_symbol(self, symbol: str, symbol_type: SymbolType = SymbolType.VARIABLE):
        """
        deprecated. use get_symbol_value
        :param symbol:
        :param symbol_type:
        :return:
        """
        return self.get_symbol_value(symbol, symbol_type)

    def get_symbol_value(self, symbol: str, symbol_type: SymbolType = SymbolType.VARIABLE):
        """
        Gets the symbols VALUE. TODO: Rename to get_symbol_value
        :param symbol:
        :return:
        """
        entry = self._get_symbol_entry(symbol, symbol_type)
        return entry.value

    def get_symbol_type(self, symbol:str, symbol_type:SymbolType=SymbolType.VARIABLE):
        """
        :param symbol:
        :return:
        """
        entry = self._get_symbol_entry(symbol, symbol_type)
        return entry.type

    def get_symbol_arg(self, symbol:str, symbol_type:SymbolType=SymbolType.VARIABLE):
        """
        :param symbol:
        :return:
        """
        entry = self._get_symbol_entry(symbol, symbol_type)
        return entry.arg

    def dump(self, indent=0):
        print('Symbol table(s):')
        for symbol_type in self._symbol_tables:
            print(F"{symbol_type}:")
            pprint.pprint(self._symbol_tables[symbol_type], indent=indent)
        if self._enclosing_scope is not None:
            print("Enclosing Scope:")
            self._enclosing_scope.dump(indent=indent+4)