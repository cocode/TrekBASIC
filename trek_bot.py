"""
This module acts as a player in the Star Trek game, for testing and code coverage purposes.

Its actions are random, not strategic, to hit more of the code - but it turns out it never wins,
so it never hits the 'win' code. It might need some changes.
"""
import random
import sys
import re
import time

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


class Player:
    def __init__(self, program, display=False):
        self.executor = TestExecutor(self, program, coverage=True)
        self._program_output = []
        self._print_buffer = ""
        self._display = display


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
        #print("Got output: ", msg)
        if "end" in kwargs:
            self._print_buffer += msg
        else:
            self._print_buffer += msg
            self._program_output.append(self._print_buffer)
            self._print_buffer = ""

    def random_command(self):
        # TODO: Need to make "XXX" (exit) command less frequent, or we will never finish a game.
        commands ="NAVSRSLRSPHATORSHEDAMCOMHLP"
        length = len(commands)/3
        index = random.randrange(length)
        cmd = commands[index*3:index*3+3]
        #print(">> ", cmd)  # Not needed, just so I can watch the game that TrekBot is playing.
        return cmd


    def game_input(self):
        """
        This method answers request for input from the game.
        :return:
        """

        last_output = self._print_buffer
        # A request for input moves you to the next line.
        self._program_output.append(self._print_buffer)
        self._print_buffer = ""
        if last_output == "COMMAND":
            return self.random_command()
        elif last_output == 'NUMBER OF UNITS TO SHIELDS':
            return str(random.randrange(0,1000))
        elif last_output == "PHOTON TORPEDO COURSE (1-9)":
            return str(random.randrange(0,20)-5)
        elif last_output == "COMPUTER ACTIVE AND AWAITING COMMAND":
            return str(random.randrange(0, 10) - 5)
        elif last_output == "COURSE (0-9)":
            return str(random.randrange(0, 12) - 2)
        elif last_output.endswith("NUMBER OF UNITS TO SHIELDS"):
            # ENERGY AVAILABLE = 3000 NUMBER OF UNITS TO SHIELDS
            # TODO parse the energy available.
            # Pick a range that includes invalid values.
            match=energy_pattern.search(last_output)
            value = int(match.group(0))
            return str(random.randrange(0, int(value*1.1)) - value*0.5)
        elif last_output == "WARP FACTOR (0-8)":
            return str(random.randrange(0, 12) - 2)
        elif last_output == "WARP FACTOR (0-0.2)":  # This happens when warp engines are damaged
            return str(random.random()/ 4)
        elif last_output == '  INITIAL COORDINATES (X,Y)' or last_output == '  FINAL COORDINATES (X,Y)':
            return str(random.randrange(0,12) - 2) + "," + str(random.randrange(0,12) - 2)
        elif last_output == "NUMBER OF UNITS TO FIRE":
            return str(random.randrange(0, 500) - 20)
        elif last_output == "LET HIM STEP FORWARD AND ENTER 'AYE'":
            return "quit"
        elif last_output == "WILL YOU AUTHORIZE THE REPAIR ORDER (Y/N)":
            if random.random() < 0.5:
                return "Y"
            else:
                return "N"

        print(F"Unknown request for input: '{last_output}'")
        sys.exit(1)


if __name__ == "__main__":
    program = load_program("superstartrek.bas")

    player = Player(program)
    total_time = time.perf_counter()
    random.seed(127)
    random.seed(128)
    count = 10
    for round in range(1,count):
        print(F"Game {round} begins.")
        game_time = time.perf_counter()

        rc = player.play_one_game()
        print(F"Game {round} completed with a status of {rc}. Time: {time.perf_counter() - game_time}")
    total_time = time.perf_counter() - total_time
    print_coverage_report(player.executor._coverage, player.executor._program, lines=True)
    print(F"Elapsed time {total_time:10.1f}s. Average: {total_time/count:10.1f}s")
