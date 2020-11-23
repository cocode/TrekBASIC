"""
This module acts as a player in the Star Trek game, for testing and code coverage purposes.

Its actions are random, not strategic, to hit more of the code - but it turns out it never wins,
so it never hits the 'win' code. It might need some changes.
"""
import random
import sys
import re
import time

from basic_types import SymbolType

energy_pattern = re.compile("[0-9]+")

from basic_interpreter import Executor
from basic_loading import load_program
from basic_shell import print_coverage_report


class TestExecutor(Executor):
    """
    This class wraps the Executor class, and allows the Player class to read responses and return commans.
    """
    def __init__(self, player, program, **kwargs):
        super().__init__(program, **kwargs)
        self._player = player
        self._cmd_map = {

        }

    def do_print(self, msg, **kwargs):
        #print(msg, **kwargs)          # Not needed, just so I can watch the game that TrekBot is playing.
        self._player.game_print(msg, **kwargs)

    def do_input(self):
        response = self._player.game_input()
        return response


class Strategy:
    def _cmd_main(player):
        pass

    def _cmd_torpedos(player):
        pass

    def _cmd_computer(player):
        pass

    def _cmd_course(player):
        pass

    def _cmd_shield_units(player):
        pass

    def _cmd_warp(player):
        pass

    def _cmd_coords(player):
        pass

    def _cmd_pha_units(player):
        pass

    def _cmd_aye(player):
        pass

    def _cmd_repair(player):
        pass

    def get_command(self, player):
        """
        Gets the next command for the game. In theory, we only need to see the program's output, but
        I am passing in player, in case I want to write a bot that cheats by looking at variables.

        :param player:
        :return:
        """
        last_output = player._program_output[-1]
        if last_output == "COMMAND":
            return self._cmd_main(player)
        elif last_output == "PHOTON TORPEDO COURSE (1-9)":
            return self._cmd_torpedos(player)
        elif last_output == "COMPUTER ACTIVE AND AWAITING COMMAND":
            return self._cmd_computer(player)
        elif last_output == "COURSE (0-9)":
            return self._cmd_course(player)
        elif last_output.endswith("NUMBER OF UNITS TO SHIELDS"):
            return self._cmd_shield_units(player)
        elif last_output == "WARP FACTOR (0-8)":
            return self._cmd_warp(player)
        elif last_output == '  INITIAL COORDINATES (X,Y)' or last_output == '  FINAL COORDINATES (X,Y)':
            return self._cmd_coords(player)
        elif last_output == "NUMBER OF UNITS TO FIRE":
            return self._cmd_pha_units(player)
        elif last_output == "LET HIM STEP FORWARD AND ENTER 'AYE'":
            return self._cmd_aye(player)
        elif last_output == "WILL YOU AUTHORIZE THE REPAIR ORDER (Y/N)":
            return self._cmd_repair(player)




class RandomStrategy(Strategy):
    """
    This class plays startrek randomly. It is specific to superstartrek.bas. Other versions may have
    minor differences that would keep this from working.

    A true "random" player would work on anything, but would get nowhere. Completely random commands
    would be syntactically invalid 99.99% of the time, so the bot would never achieve anything. This
    program has respsonses for each input that are designed to be legal about 90% of the time, so we
    normally do something valid, but still test error conditions.

    This version only achieves 91.8% code coverage, as it fails to get to all branches. I suspect it
    never wins a game, for example.
    """
    def random_command(self):
        # TODO: Need to make "XXX" (exit) command less frequent, or we will never finish a game.
        commands ="NAVSRSLRSPHATORSHEDAMCOMHLP"
        length = len(commands)/3
        index = random.randrange(length)
        cmd = commands[index*3:index*3+3]
        #print(">> ", cmd)  # Not needed, just so I can watch the game that TrekBot is playing.
        return cmd

    def _cmd_main(self, player):
        return self.random_command(self, )

    def _cmd_torpedos(self, player):
        return str(random.randrange(0,20)-5)

    def _cmd_computer(self, player):
        return str(random.randrange(0, 10) - 5)

    def _cmd_course(self, player):
        return str(random.randrange(0, 10) - 2)

    def _cmd_shield_units(self, player):
        last_output = player._program_output[-1]
        # ENERGY AVAILABLE = 3000 NUMBER OF UNITS TO SHIELDS
        # Pick a range that includes invalid values.
        match = energy_pattern.search(last_output)
        value = int(match.group(0))
        return str(random.randrange(0, int(value * 1.1)) - value * 0.5)

    def _cmd_warp(self, player):
        last_output = player._program_output[-1]
        if last_output == "WARP FACTOR (0-8)":
            return str(random.randrange(0, 12) - 2)
        elif last_output == "WARP FACTOR (0-0.2)":  # This happens when warp engines are damaged
            return str(random.random()/ 4)

    def _cmd_coords(self, player):
        return str(random.randrange(0, 12) - 2) + "," + str(random.randrange(0, 12) - 2)

    def _cmd_pha_units(self, player):
        return str(random.randrange(0, 500) - 20)

    def _cmd_aye(self, player):
        return "quit"

    def _cmd_repair(self, player):
        if random.random() < 0.5:
            return "Y"
        else:
            return "N"

    def get_command(self, player):
        """
        Gets the next command for the game. In theory, we only need to see the program's output, but
        I am passing in player, in case I want to write a bot that cheats by looking at variables.

        :param player:
        :return:
        """
        return super().get_command(player)
        last_output = player._program_output[-1]
        if last_output == "COMMAND":
            return self.random_command()


class CheatStrategy(RandomStrategy):
    """
    This class plays startrek with some mild strategy. It is specific to superstartrek.bas. Other versions may have
    minor differences that would keep this from working.

    This strategy cheats by looking at internal variables.

    It's derived from randomstrategy, so it will work, as I implmeent the functions one by one.

    """
    def __init__(self):
        self._galaxy = None

    def _setup(self, player):
        self._galaxy = player.executor.get_symbol_value("G", SymbolType.ARRAY)
        self._energy = player.executor.get_symbol_value("E", SymbolType.VARIABLE)
        self._shields = player.executor.get_symbol_value("S", SymbolType.VARIABLE)

    def _cmd_main(player):
        pass

    def _cmd_computer(player):
        pass

    def _cmd_course(player):
        pass

    def _cmd_shield_units(player):
        pass

    def _cmd_warp(player):
        pass

    def _cmd_coords(player):
        pass

    def _cmd_pha_units(player):
        pass

    def _cmd_aye(player):
        pass

    def _cmd_repair(player):
        pass

    def get_command(self, player):
        self._setup()
        # 1. Priority should be 1) Move to star base, if available and energy low, 2) set sheilds.
        if self._shield < 500:
            desired = min(500, self._energy/2)
            if desired > self._shield:
                return F"SHE {desired}"
        return super().get_command(player)


class Player:
    def __init__(self, program:list[str], strategy:Strategy, display:bool=False):
        """

        :param program: The basic program to execute
        :param strategy:
        :param display:
        """
        self.executor = TestExecutor(self, program, coverage=True)
        self._program_output = []
        self._print_buffer = ""
        self._display = display
        self._strategy = strategy

    def play_one_game(self):
        self.executor.restart()
        rc = self.executor.run_program()
        return rc

    def game_print(self, msg, **kwargs):
        """
        This method receives anything printed by the game
        :param msg:
        :return:
        """
        if "end" in kwargs:
            self._print_buffer += msg
        else:
            self._print_buffer += msg
            if self._display:
                print(">>", self._print_buffer)
            self._program_output.append(self._print_buffer)
            self._print_buffer = ""

    def get_command(self):
        strategy = self._strategy
        # Pass the player to the strategies get_command
        command = strategy.get_command(self)
        if self._display:
            print("<<", command)
        return command

    def game_input(self):
        """
        This method answers request for input from the game.
        :return:
        """

        last_output = self._print_buffer
        # A request for input completes the last line of output.
        self._program_output.append(self._print_buffer)
        self._print_buffer = ""

        command = self.get_command()
        return command


if __name__ == "__main__":
    program = load_program("superstartrek.bas")

    player_strategy = RandomStrategy()
    player = Player(program, player_strategy, display=False)
    total_time = time.perf_counter()
    random.seed(127)
    random.seed(128)
    count = 3
    for round in range(1,count):
        print(F"Game {round} begins.")
        game_time = time.perf_counter()

        rc = player.play_one_game()
        print(F"Game {round} completed with a status of {rc}. Time: {time.perf_counter() - game_time}")
    total_time = time.perf_counter() - total_time
    print_coverage_report(player.executor._coverage, player.executor._program, lines=True)
    print(F"Elapsed time {total_time:10.1f}s. Average: {total_time/count:10.1f}s")
