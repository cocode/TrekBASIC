import unittest

from basic_find_str_quotes import find_next_str_not_quoted


class TestFindNextStrNotQuoted(unittest.TestCase):
    def test_simple_outside_quotes(self):
        s = 'foo ELSE bar'
        self.assertEqual(find_next_str_not_quoted(s, 'ELSE'), (4, 8))

    def test_inside_quotes_only(self):
        s = '"ELSE"'
        self.assertEqual(find_next_str_not_quoted(s, 'ELSE'), (None, None))

    def test_mixed_quoted_and_unquoted(self):
        s = 'start "ELSE" middle ELSE end'
        # now correctly picks the first unquoted ELSE at indices 0-based 20–24
        self.assertEqual(find_next_str_not_quoted(s, 'ELSE'), (20, 24))

    def test_multiple_unquoted(self):
        s = 'ELSE one ELSE two'
        # should find the very first occurrence
        self.assertEqual(find_next_str_not_quoted(s, 'ELSE'), (0, 4))

    def test_no_occurrence(self):
        s = 'no matching word here'
        self.assertEqual(find_next_str_not_quoted(s, 'ELSE'), (None, None))

    def test_target_with_special_chars(self):
        s = 'look for +*? outside quotes +*?'
        # now that we escape the target, we do find it at the first position
        first = s.index('+*?')
        self.assertEqual(find_next_str_not_quoted(s, '+*?'), (first, first + 3))

    def test_quoted_with_escaped_quote(self):
        s = 'foo \\"ELSE\\" bar ELSE'
        # the escaped-quote syntax isn’t treated as a literal quote, so we still match the final ELSE
        idx = s.index('ELSE', 12)
        self.assertEqual(find_next_str_not_quoted(s, 'ELSE'), (idx, idx + 4))

if __name__ == '__main__':
    unittest.main()