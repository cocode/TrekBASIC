from unittest import TestCase

from basic_shell import BasicShell


class TestBasicShell(TestCase):
    def test_load(self):
        b = BasicShell("simple_test.bas")
        b.load()

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
    # def test_cmd_symbols(self):
    #     self.fail()
    #
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
