from math import pi, atan2
from unittest import TestCase
import types
import unittest

import trek_bot
from basic_interpreter import Executor
from basic_loading import load_program, tokenize
from trek_bot import CheatStrategy, Player, compute_course


class TestCheatStrategy(TestCase):
    def setUp(self):
        # Just use the lexer for convenience. We culd just create the tokens used for operands manually
        self._strategy = CheatStrategy()
        listing = [
            '100 DIMG(8,8):S=1000:E=3000:Q1=1:Q2=2:S1=3:S2=4:K3=3:Q$="ABC"',
        ]
        self._program = tokenize(listing)
        self._executor = Executor(self._program)

    def test_setup(self):
        player = Player(self._program, self._strategy, False)
        player.play_one_game()
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


    def test_angle(self):
        for dy in range(1, -2, -1):
            for dx in range(-1, 2):
                course = compute_course(dx,dy)
                print(F"{course:6.2f}   ", end="")
            print()
        self.assertEqual(1, compute_course(0, 1))
        self.assertEqual(2, compute_course(-1, 1))
        self.assertEqual(3, compute_course(-1, 0))
        self.assertEqual(4, compute_course(-1, -1))
        self.assertEqual(5, compute_course(0, -1))
        self.assertEqual(6, compute_course(1, -1))
        self.assertEqual(7, compute_course(1, 0))
        self.assertEqual(8, compute_course(1, 1))

    def test_replace_from_sector(self):
        sector = "abcdefghijklmnopqrstuvwxyz0123456789"
        self.assertEqual("abc", trek_bot.get_in_sector(sector, 0, 0))
        self.assertEqual("yz0", trek_bot.get_in_sector(sector, 1, 0))
        s2 = trek_bot.replace_from_sector(sector, 0, 7, "QWE")
        self.assertEqual("QWE", trek_bot.get_in_sector(s2, 0, 7))
        self.assertEqual(len(sector), len(s2))

    def test_find_in_sector(self):
        sector = "abc"+"def"+"ghi"+"jkl"+"mno"+"pqr"+"stu"+"vwx"+\
                 "yz0"+"123"+">!<"+"789"
        x, y = trek_bot.find_in_sector(sector, ">!<")
        self.assertEqual(1, x)
        self.assertEqual(2, y)

    def test_find_something_current_quadrant(self):
        # Create a galaxy where the current quadrant already contains a Klingon (value >=100)
        galaxy = [[0 for _ in range(8)] for _ in range(8)]
        Q1, Q2 = 2, 3
        galaxy[Q1][Q2] = 100  # one Klingon
        self._strategy._galaxy = galaxy

        result = self._strategy.find_something(trek_bot.klingon_count, Q1, Q2)
        self.assertEqual((Q1, Q2), result, "Should find Klingon in current quadrant")

    def test_find_something_scan(self):
        # Galaxy with a Klingon located at a different quadrant than the Enterprise
        galaxy = [[0 for _ in range(8)] for _ in range(8)]
        target_x, target_y = 5, 1
        galaxy[target_x][target_y] = 100
        Q1, Q2 = 0, 0  # Enterprise starting quadrant (no Klingons here)
        self._strategy._galaxy = galaxy

        result = self._strategy.find_something(trek_bot.klingon_count, Q1, Q2)
        self.assertEqual((target_x, target_y), result, "Should scan galaxy and find first Klingon")

    def test_find_me_a_target(self):
        # Place the Enterprise at (1,1) and a Klingon at (2,2)
        galaxy = [[0 for _ in range(8)] for _ in range(8)]
        galaxy[2][2] = 100
        Q1, Q2 = 1, 1
        self._strategy._galaxy = galaxy

        cmd = self._strategy.find_me_a_target(Q1, Q2)
        # Expect navigation command
        self.assertEqual("NAV", cmd, "find_me_a_target should request NAV command")

        # Check that course and distance were computed correctly
        expected_dx, expected_dy = 1, 1
        expected_course = compute_course(expected_dx, expected_dy)
        self.assertEqual(expected_course, self._strategy._course, "Incorrect course calculated")
        from math import sqrt as _sqrt
        self.assertAlmostEqual(_sqrt(2), self._strategy._distance, places=5, msg="Incorrect distance calculated")

    def test_torpedo_course_calculation(self):
        strat = CheatStrategy()
        strat._S1, strat._S2 = 0, 6  # Enterprise sector coords
        sector = ["   "]*64  # dummy sector string placeholder
        # Build a sector string with a Klingon at (6,3)
        base = ["   "]*64
        kx, ky = 6, 3
        idx = kx*8 + ky
        base[idx] = "+K+"
        sector_str = "".join(base)
        strat._sector = sector_str
        # Compute course using internal method
        course_str = strat._cmd_torpedos(player=None)
        course = float(course_str)
        # Expected course should be about 6.4 (dy=-3,dx=6)
        from trek_bot import compute_course
        expected = compute_course(-3,6)
        self.assertAlmostEqual(expected, course, places=4)

    def test_warp_engines_damaged_flag(self):
        strat = CheatStrategy()
        # Simulate damage flag set via message detection
        strat._warp_damaged = True
        # _cmd_warp should return 0.2 and clear the flag
        response = strat._cmd_warp(player=types.SimpleNamespace(_program_output=["WARP FACTOR (0-8)?"]))
        self.assertEqual("0.2", response)
        self.assertFalse(strat._warp_damaged)

    @unittest.skip("Complex mocking required; behaviour covered in integration runs")
    def test_state_base_when_weapons_disabled(self):
        pass


