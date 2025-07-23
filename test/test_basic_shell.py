from unittest import TestCase

from trekbasicpy.basic_shell import BasicShell


class TestBasicShell(TestCase):
    def test_file_not_found(self):
        b = BasicShell("../does_not_exist.bas")
        self.assertFalse(b.load_status)

    def test_load(self):
        b = BasicShell("./programs/simple_test.bas")
        b.load_from_file()
        self.assertTrue(b.load_status)

    def test_build_line_map(self):
        listing = [
            '1 GOTO 1',
            '2 END',
        ]
        b = BasicShell()
        b.load_from_string(listing)
        start_line = 100
        increment = 10
        line_map, statement_count = b.build_line_map(b.executor._program, start_line, increment)
        self.assertEqual({1:100,2: 110}, line_map)
        new_program = b.renumber(b.executor._program, line_map, start_line, increment)
        for line in new_program:
            print(line)

        output_listing = [line.source for line in new_program]
        expected = """100 GOTO 100\n110 END\n"""
        self.assertEqual(expected, "\n".join(output_listing) + "\n")

    def test_format(self):
        listing = [
            '1 GOTO1',
            '2 PRINT     "A";"B"',
            '3 DIM A( 10 )'
        ]
        b = BasicShell()
        b.load_from_string(listing)
        new_program = b.format(b.executor._program)
        output_listing = [line.source for line in new_program]
        expected = """1 GOTO 1
2 PRINT "A"; "B"
3 DIM A(10)
"""
        self.assertEqual(expected, "\n".join(output_listing)+"\n")



    # def test_usage(self):
    #     self.fail()
    #
    # def test_cmd_load(self):
    #     self.fail()
    #
    # def test_print_current(self):
    #     self.fail()
    #
    # def test_cmd_list(self):
    #     self.fail()
    #
    # def test_format_cl(self):
    #     self.fail()
    #
    # def test_cmd_for_stack(self):
    #     self.fail()
    #
    # def test_cmd_gosub_stack(self):
    #     self.fail()
    #
    # def test_cmd_quit(self):
    #     self.fail()
    #
    def test_cmd_symbols(self):
        # Just so it gets called.
        b = BasicShell("./programs/simple_test.bas")
        self.assertTrue(b.load_status)
        # print symbols for check.
        # b.cmd_symbols(None)


    # def test_cmd_print(self):
    #     self.fail()
    #
    # def test_cmd_next(self):
    #     self.fail()
    #
    # def test_cmd_run(self):
    #     self.fail()
    #
    # def test_cmd_break(self):
    #     self.fail()
    #
    # def test_cmd_help(self):
    #     self.fail()
    #
    # def test_find_command(self):
    #     self.fail()
    #
    # def test_do_command(self):
    #     self.fail()
