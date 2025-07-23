from unittest import TestCase

from trekbasicpy.basic_utils import smart_split


class Test(TestCase):

    def test_smart_split(self):
        line = 'PRINT"YOUR MISSION: BEGINS":PRINT"AND ENDS"'
        results = smart_split(line)
        self.assertEqual(2, len(results))
        self.assertEqual('PRINT"YOUR MISSION: BEGINS"', results[0])
        self.assertEqual('PRINT"AND ENDS"', results[1])

        line = "G(8,8),C(9,2),K(3,3),N(3),Z(8,8),D(8)"
        results = smart_split(line,enquote="(", dequote=")", split_char=",")
        self.assertEqual(6, len(results))
        self.assertEqual('G(8,8)', results[0])
        self.assertEqual('C(9,2)', results[1])

    # TODO: Uncomment these tests as we implement IF THEN ELSE support in smart_split
    
    def test_smart_split_if_then_else_basic(self):
        """Test basic IF THEN ELSE without colons"""
        line = 'IF A>0 THEN PRINT "Positive" ELSE PRINT "Not positive"'
        results = smart_split(line)
        self.assertEqual(1, len(results))
        self.assertEqual('IF A>0 THEN PRINT "Positive" ELSE PRINT "Not positive"', results[0])

    # def test_smart_split_if_then_else_with_colons_in_then(self):
    #     """Test IF THEN ELSE with multiple statements in THEN clause"""
    #     line = 'IF A>0 THEN PRINT "Positive": B=1 ELSE PRINT "Not positive"'
    #     results = smart_split(line)
    #     self.assertEqual(1, len(results))
    #     self.assertEqual('IF A>0 THEN PRINT "Positive": B=1 ELSE PRINT "Not positive"', results[0])

    # def test_smart_split_if_then_else_with_colons_in_else(self):
    #     """Test IF THEN ELSE with multiple statements in ELSE clause"""
    #     line = 'IF A>0 THEN PRINT "Positive" ELSE PRINT "Not positive": B=0'
    #     results = smart_split(line)
    #     self.assertEqual(1, len(results))
    #     self.assertEqual('IF A>0 THEN PRINT "Positive" ELSE PRINT "Not positive": B=0', results[0])

    # def test_smart_split_if_then_else_with_colons_both(self):
    #     """Test IF THEN ELSE with multiple statements in both clauses"""
    #     line = 'IF A>0 THEN PRINT "Positive": B=1 ELSE PRINT "Not positive": B=0'
    #     results = smart_split(line)
    #     self.assertEqual(1, len(results))
    #     self.assertEqual('IF A>0 THEN PRINT "Positive": B=1 ELSE PRINT "Not positive": B=0', results[0])

    def test_smart_split_if_then_else_with_statements_after(self):
        """Test IF THEN ELSE followed by other statements"""
        line = 'IF A>0 THEN B=1 ELSE B=0: PRINT B: GOTO 100'
        results = smart_split(line)
        self.assertEqual(3, len(results))
        self.assertEqual('IF A>0 THEN B=1 ELSE B=0', results[0])
        self.assertEqual(' PRINT B', results[1])
        self.assertEqual(' GOTO 100', results[2])

    # def test_smart_split_multiple_if_then_else(self):
    #     """Test multiple IF THEN ELSE statements on one line"""
    #     line = 'IF A>0 THEN B=1 ELSE B=0: IF C>0 THEN D=1 ELSE D=0'
    #     results = smart_split(line)
    #     self.assertEqual(2, len(results))
    #     self.assertEqual('IF A>0 THEN B=1 ELSE B=0', results[0])
    #     self.assertEqual(' IF C>0 THEN D=1 ELSE D=0', results[1])

    def test_smart_split_if_then_without_else(self):
        """Test IF THEN without ELSE (should split at colons as before)"""
        line = 'IF A>0 THEN PRINT "Positive": B=1'
        results = smart_split(line)
        self.assertEqual(2, len(results))
        self.assertEqual('IF A>0 THEN PRINT "Positive"', results[0])
        self.assertEqual(' B=1', results[1])

    # def test_smart_split_mixed_if_statements(self):
    #     """Test mix of IF THEN ELSE and IF THEN statements"""
    #     line = 'IF A>0 THEN B=1: IF C>0 THEN D=1 ELSE D=0: PRINT "Done"'
    #     results = smart_split(line)
    #     self.assertEqual(3, len(results))
    #     self.assertEqual('IF A>0 THEN B=1', results[0])
    #     self.assertEqual(' IF C>0 THEN D=1 ELSE D=0', results[1])
    #     self.assertEqual(' PRINT "Done"', results[2])

    def test_smart_split_else_in_string_literals(self):
        """Test that ELSE inside string literals doesn't confuse the parser"""
        line = 'IF A>0 THEN PRINT "ELSE is a keyword" ELSE PRINT "THEN is too"'
        results = smart_split(line)
        self.assertEqual(1, len(results))
        self.assertEqual('IF A>0 THEN PRINT "ELSE is a keyword" ELSE PRINT "THEN is too"', results[0])

    # def test_smart_split_nested_if_then_else(self):
    #     """Test nested IF THEN ELSE - now raises error since multiple IFs not supported"""
    #     line = 'IF A>0 THEN IF B>0 THEN C=1 ELSE C=0 ELSE C=2'
    #     with self.assertRaises(ValueError):
    #         smart_split(line)

    # def test_smart_split_complex_nested_with_colons(self):
    #     """Test complex nested IF with colons in various places"""
    #     line = 'IF A>0 THEN IF B>0 THEN C=1: D=2 ELSE C=0 ELSE C=2: PRINT C'
    #     results = smart_split(line)
    #     self.assertEqual(2, len(results))
    #     self.assertEqual('IF A>0 THEN IF B>0 THEN C=1: D=2 ELSE C=0 ELSE C=2', results[0])
    #     self.assertEqual(' PRINT C', results[1])

