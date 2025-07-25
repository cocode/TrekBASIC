"""
This module acts as a player in the Star Trek game, for testing and code coverage purposes.

Its actions are random, not strategic, to hit more of the code - but it turns out it never wins,
so it never hits the 'win' code. It might need some changes.
"""
import random
import re
import sys
import time
from enum import Enum, auto
from math import atan2, pi, sqrt

from trekbasicpy.basic_dialect import DIALECT
from trekbasicpy.basic_types import SymbolType, Program

from trekbasicpy.basic_interpreter import Executor
from trekbasicpy.basic_loading import load_program
from trekbasicpy.basic_shell import print_coverage_report, generate_html_coverage_report

energy_pattern = re.compile("[0-9]+")

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
        # print(msg, **kwargs)          # Not needed, just so I can watch the game that TrekBot is playing.
        self._player.game_print(msg, **kwargs)

    def do_input(self):
        response = self._player.game_input()
        assert response is not None
        return response


class Strategy:
    def _cmd_main(self, player):
        pass

    def _cmd_torpedos(self, player):
        pass

    def _cmd_computer(self, player):
        pass

    def _cmd_course(self, player):
        pass

    def _cmd_shield_units(self, player):
        pass

    def _cmd_warp(self, player):
        pass

    def _cmd_coords(self, player):
        pass

    def _cmd_pha_units(self, player):
        pass

    def _cmd_aye(self, player):
        pass

    def _cmd_repair(self, player):
        pass

    def _cmd_energy(self, player):
        pass

    def get_command(self, player):
        command = self.get_command2(player)
        if command is not None:
            return command

        # should not get here. Print info, and exit
        last_output = player._program_output[-1].rstrip()
        print("Last output:", last_output)
        command = self.get_command2(player)

        sys.exit(99)

    def get_command2(self, player):
        """
        Gets the next command for the game. In theory, we only need to see the program's output, but
        I am passing in player, in case I want to write a bot that cheats by looking at variables.

        :param player:
        :return:
        """
        last_output = player._program_output[-1].rstrip()
        if last_output == "COMMAND":
            return self._cmd_main(player)
        elif last_output == "SHIELD CONTROL INOPERABLE": # I don;t think this can happen. It always prints "COMMAND" after an error
            # TODO Should check all the error messages to COMMAND, like "SHIELD CONTROL INOPERABLE", and handle them.
            return self._cmd_main(player) # Pick a different command.
        elif last_output == "PHOTON TORPEDO COURSE (1-9)":
            return self._cmd_torpedos(player)
        elif last_output == "COMPUTER ACTIVE AND AWAITING COMMAND":
            return self._cmd_computer(player)
        elif last_output == "COURSE (0-9)":
            return self._cmd_course(player)
        elif last_output.endswith("NUMBER OF UNITS TO SHIELDS"):
            return self._cmd_shield_units(player)
        elif last_output == "WARP FACTOR (0-8)?" or last_output == 'WARP FACTOR (0-0.2)?':
            return self._cmd_warp(player)
        elif last_output == '  INITIAL COORDINATES (X,Y)' or last_output == '  FINAL COORDINATES (X,Y)':
            return self._cmd_coords(player)
        elif last_output == "NUMBER OF UNITS TO FIRE":
            return self._cmd_pha_units(player)
        elif last_output == "LET HIM STEP FORWARD AND ENTER 'AYE'":
            return self._cmd_aye(player)
        elif last_output == "WILL YOU AUTHORIZE THE REPAIR ORDER (Y/N)":
            return self._cmd_repair(player)
        elif last_output.startswith("ENERGY AVAILABLE = "):
            energy_start = last_output[19:]
            energy_end = energy_start.find(" ")
            energy_value = int(energy_start[:energy_end+1])
            return self._cmd_energy(energy_value)

        raise Exception(F"Unknown prompt in trek_bot: '{last_output}'")



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
        length = len(commands)//3
        index = random.randrange(length)
        cmd = commands[index*3:index*3+3]
        #print(">> ", cmd)  # Not needed, just so I can watch the game that TrekBot is playing.
        return cmd

    def _cmd_main(self, player):
        return self.random_command()

    def _cmd_torpedos(self, player):
        return str(random.randrange(0,10)-2)

    def _cmd_computer(self, player):
        # super star trek has a bug here. It can handle negative numbers,
        # and returns an error, but anything larger than 5 and it will crash.
        return str(random.randrange(0, 7) - 2)

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
        if last_output == "WARP FACTOR (0-8)? ":
            return str(random.randrange(0, 12) - 2)
        elif last_output == "WARP FACTOR (0-0.2)? ":  # This happens when warp engines are damaged
            return str(random.random()/ 4)
        else:
            raise Exception(F"Unknown warp prompt in trek_bot: '{last_output}'")

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

    def cmd_energy(self, energy_value):
        rand_num = random.randint(1, energy_value)
        return str(rand_num)


    def get_command(self, player):
        """
        Gets the next command for the game. In theory, we only need to see the program's output, but
        I am passing in player, in case I want to write a bot that cheats by looking at variables.

        :param player:
        :return:
        """
        return super().get_command(player)


# Count of kingons in a sector.
def klingon_count(x): return x//100

def compute_course(dy:int, dx:int):
    # The grid layout in this program has x for y, and positive is down, not up, so we have to adjust
    #dx, dy = dy, dx
    dy = -dy

    at = atan2(dy, dx)
    course = at * 4 / pi
    if course < 0:
        course = 8 + course
    course = course + 1  # convert 0 <= course < 8 to 1 <= course < 9
    return course

def get_in_sector(sector:str, x:int,y:int):
    """

    :param sector: A string representation of the current sector.
    :param x: 0-based index into sector
    :param y:
    :return:
    """
    assert sector is not None
    assert 0 <= x < 8
    assert 0 <= y < 8
    index = x * 24 + y * 3
    assert 0 <= index < len(sector) - 3
    return sector[index:index+3]


def replace_from_sector(sector: str, x: int, y: int, value:str):
    """

    :param sector: A string representation of the current sector.
    :param x: 0-based index into sector
    :param y:
    :return: A new str for the sector. NOT in place replacement
    """
    assert sector is not None
    assert len(value) == 3
    assert 0 <= x < 8
    assert 0 <= y < 8
    index = x * 24 + y * 3
    assert 0 <= index < len(sector) - 3
    return sector[0:index] + value + sector[index + 3:]


def find_in_sector(sector, target):
    assert len(target) == 3
    index = sector.find(target)
    assert index != -1
    assert index % 3 == 0
    index = index / 3
    x = index // 8
    y = index % 8
    return x,y

def print_galaxy(g, enterprise_x, enterprise_y):
    for i in range(0,8):
        for j in range(0,8):
            spot = "*" if i==enterprise_x and j==enterprise_y else " "
            print(F"{int(g[i][j]):5}{spot}", end="")
        print()

class CheatState(Enum):
    SHIELDS = auto()
    BASE = auto()
    HUNT = auto()
    KILL = auto()


class CheatStrategy(RandomStrategy):
    """
    This class plays startrek with some mild strategy. It is specific to superstartrek.bas. Other versions may have
    minor differences that would keep this from working.

    This strategy cheats by looking at internal variables. This is mostly for convenience, you can
    parse most of this from the output, but that's more work.

    It's derived from randomstrategy, so it will work, as I implmeent the functions one by one.

    """
    def __init__(self):
        self._galaxy = None
        self._state = CheatState.SHIELDS
        self._warp_damaged = False  # remembers if engines were reported damaged
        self._warp_retry = False

    def _setup(self, player):
        self._galaxy = player.executor.get_symbol_value("G", SymbolType.ARRAY)
        self._energy = player.executor.get_symbol_value("E", SymbolType.VARIABLE)
        self._shields = player.executor.get_symbol_value("S", SymbolType.VARIABLE)
        self._Q1 = int(player.executor.get_symbol_value("Q1", SymbolType.VARIABLE)) - DIALECT._ARRAY_OFFSET
        self._Q2 = int(player.executor.get_symbol_value("Q2", SymbolType.VARIABLE)) - DIALECT._ARRAY_OFFSET
        self._S1 = int(player.executor.get_symbol_value("S1", SymbolType.VARIABLE)) - DIALECT._ARRAY_OFFSET
        self._S2 = int(player.executor.get_symbol_value("S2", SymbolType.VARIABLE)) - DIALECT._ARRAY_OFFSET
        self._K3 = int(player.executor.get_symbol_value("K3", SymbolType.VARIABLE))
        self._sector = player.executor.get_symbol_value("Q$", SymbolType.VARIABLE)
        # Device damage array (1-based in BASIC). <0 means inoperable
        try:
            self._device_damage = player.executor.get_symbol_value("D", SymbolType.ARRAY)
            # Adjust for BASIC 1-based indexing using ARRAY_OFFSET
            phaser_idx = 4 - DIALECT._ARRAY_OFFSET
            torp_idx = 5 - DIALECT._ARRAY_OFFSET
            self._phasers_disabled = self._device_damage[phaser_idx] < 0
            self._torps_disabled = self._device_damage[torp_idx] < 0
        except Exception:
            # Fallback: assume operational if array not available (unit tests)
            self._phasers_disabled = False
            self._torps_disabled = False
        # Also consider no torpedoes remaining
        try:
            self._torps_disabled = self._torps_disabled or player.executor.get_symbol_value("P", SymbolType.VARIABLE) <= 0
        except Exception:
            pass

    def random_command(self):
        commands = ["NAV", "SRS","LRS","PHA","TOR","SHE","DAM","COM","HLP","XXX"]
        weights  = [1000,    100,  200,  500,   50,   10,   10,   50,    1,    1]
        cmd = random.choices(commands, weights=weights, k=1)
        return cmd[0]

    def find_something(self, break_func, Q1, Q2):
        """
        Finds the first starbase, or klingon. Depends on break_func.
        Should find the NEAREST. Current we just start at quadrant 0,0 and scan.
        Adding "Check the current sector first"
        TODO: If looking for starbases, prefer ones that don't have klingons.
        TODO: Find the nearest starbase that doesn't have stars in my way. IIRC the game only
        checks to see if there are stars in your path in your current sector.

        :param break_func: Function that tells us when we have found what we are looking for.
        :param Q1: X quadrant of enterprise
        :param Q2: Y quadrant of enterprise.
        :return: tuple of course (1-8) and distance.
        """
        if break_func(self._galaxy[Q1][Q2]):
            return Q1, Q2
        for i in range(0, 8):
            for j in range(0, 8):
                if break_func(self._galaxy[i][j]):
                    return i, j
        return None

    def _cmd_main(self, player):
        last_output = player._program_output[-1]
        before_last = player._program_output[-2]
        # Detect engine-damage message from previous line
        if before_last.startswith("WARP ENGINES ARE DAMAGED"):
            self._warp_damaged = True
        # Detect chief engineer warp refusal message
        if before_last.strip().startswith("CHIEF ENGINEER SCOTT REPORTS") and "ENGINES WON'T TAKE WARP" in before_last:
            self._warp_retry = True
        Q1 = self._Q1
        Q2 = self._Q2
        if Q1 < 0 or Q1 > 7 or Q2 < 0 or Q2 > 7:
            print("Quadrant out of range")
        S1 = self._S1
        S2 = self._S2
        if S1 < 0 or S1 > 7 or S2 < 0 or S2 > 7:
            print("Sector out of range")
        galaxy = self._galaxy
        sector_value = galaxy[Q1][Q2] # I think that's a quadrant, not sector.
        print("Value for current quadrant: ", sector_value)
        print_galaxy(self._galaxy, Q1, Q2)

        if self._warp_damaged:
            # primary goal: reach starbase for repairs
            self._state = CheatState.BASE
        elif self._phasers_disabled and self._torps_disabled:
            self._state = CheatState.BASE
        elif self._shields < 500 and self._energy > 3 * self._shields and before_last != "SHIELD CONTROL INOPERABLE":
            self._state = CheatState.SHIELDS
        elif self._energy < 1000:
            self._state = CheatState.BASE
        elif klingon_count(sector_value) > 0:
            print("Klingon count, this quadrant: ", klingon_count(sector_value))
            # TODO Chose more carefully between fight or flight.
            self._state = CheatState.KILL
        else:
            self._state = CheatState.HUNT
        print("Current state is: ", self._state)
        if self._state == CheatState.SHIELDS:
            # 1. Priority should be 1) Move to star base, if available and energy low, 2) set sheilds.
            if self._shields < 500:
                if len(player._program_output) > 2 and player._program_output[-2] != "SHIELD CONTROL INOPERABLE":
                    desired = min(500, self._energy/2)
                    #print("Trek bot thinks shields are low.", self._shields, desired)
                    if desired > self._shields:
                        return "SHE"

        # If there are klingons in the section, kill.
        if self._state == CheatState.KILL:
            # Prefer available weapon
            if self._phasers_disabled and not self._torps_disabled:
                return "TOR"
            if self._torps_disabled and not self._phasers_disabled:
                return "PHA"
            if self._phasers_disabled and self._torps_disabled:
                # Shouldn't happen due to state override, but safe guard
                return self.find_me_a_target(Q1, Q2)
            # both available – random choice
            if random.random() < 0.5:
                return "TOR"
            return "PHA"

        # TODO Hunt for starbase if energy is low.
        if self._state == CheatState.BASE:
            def extract_bases(x):
                return (x//10) % 10
            target = self.find_something(extract_bases, Q1, Q2)
            if target is None:
                print("No starbases found!!")
                return self.random_command()
            if target == (Q1, Q2):
                # We have a starbase in this quadrant, need to dock.
                print("Need to dock")
                # Find base position
                x, y = find_in_sector(self._sector, ">!<")
                assert 0 <= x < 8
                assert 0 <= y < 8
                # Find delta x,y
                dx = x - S1
                dy = y - S2
                # plot course (later watch for stars in the way)
                self._course = compute_course(dx, dy)
                # Move to base
                self._distance = sqrt(dx * dx + dy * dy) /  8
                return "NAV"

            # Save course to set in next command
            dx = (target[0]) - Q1
            dy = (target[1]) - Q2
            if dx or dy:
                print(F"BASE: From: Q {Q1}, {Q2} to {target[0]}, {target[1]}. Delta {dx}, {dy}")
                self._course = compute_course(dx, dy)
                self._distance = sqrt(dx * dx + dy * dy)  # this is overshooting, somehow.
                return "NAV"

            print(F"BASE: From: S {S1}, {S2} to {target[0]}, {target[1]}. Delta {dx}, {dy}")
            self._course = compute_course(dx, dy)
            self._distance = sqrt(dx * dx + dy * dy) /8
            return "NAV"

        # If there are no klingons in the section
        if self._state == CheatState.HUNT:
            return self.find_me_a_target(Q1, Q2)

        return self.random_command()

    def find_me_a_target(self, Q1, Q2):
        target = self.find_something(klingon_count, Q1, Q2)
        if target is None:
            print("ERROR: No more Klingons but game is not over.")
            return super().get_command()
        # Save course to set in next command
        dx = (target[0]) - Q1
        dy = (target[1]) - Q2
        print(F"HUNT: From: {Q1}, {Q2} to {target[0]}, {target[1]}. Delta {dx}, {dy}")
        self._course = compute_course(dx, dy)
        self._distance = sqrt(dx * dx + dy * dy)  # this is overshooting, somehow.
        return "NAV"

    # def _cmd_computer(self, player):
    #     pass
    #
    def _cmd_course(self, player):
        course = self._course
        self._course = None
        if course is None or random.random() < 0.05:
            return super()._cmd_course(player)
        return str(course)

    def _cmd_warp(self, player):
        if self._warp_retry:
            # Choose a safe random warp 0-8
            self._warp_retry = False
            print("random is ", random)
            print("round is ", round)
            print("str is ", str)
            return str(round(random.uniform(0, 8), 2))
        # If engines were damaged, only allow 0.2 and clear the flag
        if self._warp_damaged:
            self._warp_damaged = False
            return "0.2"
        if player._program_output[-1] == "WARP FACTOR (0-0.2)":
            return "0.2"
        distance = self._distance
        if distance is None:
            return super()._cmd_warp(player)
        self._distance = None
        if distance == 0:
            print("Zero distance.")
        return str(distance)

    def _cmd_shield_units(self, player):
        desired = min(500, self._energy/2)
        return F"{desired}"

    #
    # def _cmd_coords(self, player):
    #     pass
    #
    def _cmd_pha_units(self, player):
        # TODO Should check output [-1] for an error messge about exceeding ENERGY AVAILABLE
        return str(int(min(200, self._energy * 0.5)))

    #
    # def _cmd_aye(self, player):
    #     pass
    #
    # def _cmd_repair(self, player):
    #     pass

    def _cmd_torpedos(self, player):
        x, y = find_in_sector(self._sector, "+K+")
        dx = x - self._S1
        dy = y - self._S2
        course = compute_course(dy, dx)
        print(F"Enterprise at ({self._S1}, {self._S2}) Klingon at: ({x}, {y}), Delta: ({dx}, {dy}) course: {course}")
        return str(course)

    def get_command(self, player):
        self._setup(player)
        return super().get_command(player)


class Player:
    def __init__(self, program:Program, strategy:Strategy, display:bool=False):
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

    def _flush_print_buffer(self):
        if self._display:
            print(">>", self._print_buffer)
        self._program_output.append(self._print_buffer)
        self._print_buffer = ""

    def game_print(self, msg, **kwargs):
        """
        This method receives anything printed by the game
        :param msg:
        :return:
        """
        self._print_buffer += msg
        if 'end' not in kwargs:
            self._flush_print_buffer()

    def get_command(self):
        strategy = self._strategy
        # Pass the player to the strategies get_command
        command = strategy.get_command(self)
        assert command is not None
        if self._display:
            print("<<", command)
        if command is None:
            print("Bad command (None)")
        return command

    def game_input(self):
        """
        This method answers request for input from the game.
        :return:
        """
        self._flush_print_buffer()
        last_output = self._program_output[-1]
        command = self.get_command()
        return command


def go():
    program = load_program("programs/superstartrek.bas")

    # player_strategy = RandomStrategy()
    player_strategy = CheatStrategy()
    player = Player(program, player_strategy, display=True)
    total_time = time.perf_counter()
    random.seed(127)
    random.seed(128)
    count = 10
    for game_round in range(1, count + 1):
        print(F"Game {game_round} begins.")
        game_time = time.perf_counter()

        rc = player.play_one_game()
        print(F"Game {game_round} completed with a status of {rc}. Time: {time.perf_counter() - game_time:.2f} seconds.")
    total_time = time.perf_counter() - total_time
    print_coverage_report(player.executor._coverage, player.executor._program)
    generate_html_coverage_report(player.executor._coverage, player.executor._program, "trek_coverage_report.html")
    print(F"Elapsed time {total_time:10.1f}s. Average: {total_time/count:10.1f}s")

if __name__ == "__main__":
    go()