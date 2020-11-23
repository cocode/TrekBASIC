from unittest import TestCase

from basic_interpreter import Executor
from basic_loading import load_program, tokenize
from trek_bot import CheatStrategy, Player



class TestCheatStrategy(TestCase):
    def setUp(self):
        # Just use the lexer for convenience. We culd just create the tokens used for operands manually
        self._strategy = CheatStrategy()
        listing = [
            '100 DIMG(8,8):S=1000:E=3000',
        ]
        self._program = tokenize(listing)
        self._executor = Executor(self._program)

    def test_setup(self):
        player = Player(self._program, self._strategy, False)
        player.play_one_game()
        player.executor._symbols.dump()
        self._strategy._setup(player)
        self.assertTrue(type(self._strategy._galaxy)== list, "Wrong type for galaxy")
        self.assertTrue(type(self._strategy._energy)== float, "Wrong type for energy")
        self.assertTrue(type(self._strategy._shields)== float, "Wrong type for shields")

    def test__cmd_main(self):
        pass

    def test__cmd_computer(self):
        pass

    def test__cmd_course(self):
        pass

    def test__cmd_shield_units(self):
        pass

    def test__cmd_warp(self):
        pass

    def test__cmd_coords(self):
        pass

    def test__cmd_pha_units(self):
        pass

    def test__cmd_aye(self):
        pass

    def test__cmd_repair(self):
        pass

    def test_get_command(self):
        pass
