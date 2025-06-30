import unittest
from unittest import TestCase
from basic_shell import BasicShell
from basic_loading import tokenize

# test renumbering empty program.

class TestRenumber(TestCase):
    
    def setUp(self):
        """Set up a BasicShell instance for testing"""
        self.shell = BasicShell()

    def test_build_line_map(self):
        """Test basic renumbering functionality"""
        # Load a simple program
        program_lines = [
            "1 A=1:B=2:C=3",
            "2 PRINT \"WORLD\"",
            "3 END"
        ]

        # Load the program into the shell
        self.shell.load_from_string(program_lines)
        source_program_lines = self.shell.executor._program
        line_map, statement_count = self.shell.build_line_map(source_program_lines, 137, 10)
        self.assertEqual(len(line_map), len(program_lines))
        self.assertEqual(5, statement_count)

    def test_smart_join(self):
        """
        Test the smart join functionality. Note that this test is brittle. What is returned from smart_join
        is a cleaned-up version of what went in, not the original source. So, if the output format is
        changed, this test will break. See smart_join().
        """
        program_lines = [
            '1 IF 1=1 THEN PRINT "7"',
            '20 LET A=3:LET B=4:IF A=B THEN PRINT "8"',
        ]
        # Load the program into the shell
        self.shell.load_from_string(program_lines)
        p = self.shell.executor._program
        line0 = "1 " + self.shell.smart_join(p[0].stmts)
        line1 = "20 " + self.shell.smart_join(p[1].stmts)

        self.assertEqual(program_lines[0], line0)
        self.assertEqual(program_lines[1], line1)

    # def test_renumber(self):
    #     """
    #     Test the underlying renumber functionality.
    #     This just tests to see if renumber doesn't change anything when it
    #     doesn't have to. But it requires implementing PreparedStatementXX.__eq__ for all
    #     of them.,
    #     """
    #     line_map: dict[int:int] = {1: 100}
    #     old_program_lines = ["100 IF 1=2 THEN PRINT 3"]
    #     self.shell.load_from_string(old_program_lines)
    #     old_program = self.shell.executor._program
    #     self.shell.executor.run_program()
    #     self.shell.load_from_string(old_program_lines)
    #     new_program = self.shell.renumber(old_program=old_program,
    #                                       line_map=line_map,
    #                                       start_line=100,
    #                                       increment=10)
    #     self.assertEqual(old_program, new_program, )

    def test_simple_renumber(self):
        """Test basic renumbering functionality"""
        # Load a simple program
        program_lines = [
            "100 PRINT \"HELLO\"",
            "200 PRINT \"WORLD\"",
            "300 END"
        ]
        
        # Load the program into the shell
        self.shell.load_from_string(program_lines)
        
        # Get initial line count
        initial_count = len(self.shell.executor._program)
        
        # Renumber
        self.shell.cmd_renum(None, False)
        
        # Check that we have the same number of lines
        final_count = len(self.shell.executor._program)
        self.assertEqual(initial_count, final_count, "Line count should not change after renumbering")
        
        # Check that lines are properly renumbered
        lines = [line.line for line in self.shell.executor._program]
        self.assertEqual(lines, [100, 110, 120], f"Lines should be renumbered to 100, 110, 120, got {lines}")

    def test_for_loop_renumber(self):
        """Test renumbering programs with FOR loops"""
        program_lines = [
            "1000 FOR I = 1 TO 10",
            "1010 PRINT I",
            "1020 NEXT I",
            "1030 END"
        ]
        
        self.shell.load_from_string(program_lines)
        
        initial_count = len(self.shell.executor._program)
        
        # Renumber
        self.shell.cmd_renum(None, False)
        
        final_count = len(self.shell.executor._program)
        self.assertEqual(initial_count, final_count, "FOR loop program line count should not change")
        
        # Check that the FOR loop structure is preserved
        program_text = []
        for line in self.shell.executor._program:
            statements = []
            for stmt in line.stmts:
                statements.append(str(stmt))
            program_text.append(f"{line.line} {' : '.join(statements)}")
        
        # Verify FOR loop keywords are preserved
        self.assertTrue(any("FOR" in line for line in program_text), "FOR keyword should be preserved")
        self.assertTrue(any("NEXT" in line for line in program_text), "NEXT keyword should be preserved")

    def test_if_then_renumber(self):
        """Test renumbering programs with IF THEN statements"""
        program_lines = [
            "100 FOR J = 3 TO 3",
            "110 IF J <> 3 THEN STOP",
            "120 NEXT J",
            "130 END"
        ]

        self.shell.load_from_string(program_lines)
        
        initial_count = len(self.shell.executor._program)

        # Renumber
        self.shell.cmd_renum(None, False)

        final_count = len(self.shell.executor._program)
        self.assertEqual(initial_count, final_count, "IF THEN program line count should not change")
        
        # Check that we don't have any extra STOP statements
        program_text = []
        for line in self.shell.executor._program:
            statements = []
            for stmt in line.stmts:
                statements.append(str(stmt))
            program_text.append(f"{line.line} {' : '.join(statements)}")
        
        # Count STOP statements
        stop_count = sum(line.count("STOP") for line in program_text)
        self.assertEqual(stop_count, 1, f"Should have exactly 1 STOP statement, found {stop_count}")

    def test_complex_program_renumber(self):
        """Test renumbering the specific problematic program from the bug report"""
        program_lines = [
            "1000 REM check limits on for loops",
            "1101 FOR J = 3 TO 3 STEP 1",
            "1102 IF J <> 3 THEN STOP",
            "1103 NEXT J",
            "1200 S = 0",
            "1204 FOR J=1 TO 10",
            "1205 S = S + J",
            "1206 NEXT J",
            "1207 PRINT \"AFTER LOOP 2 S==\";S",
            "1208 IF S <> 55 THEN PRINT \"FIRST ERROR,SB 55\";S:STOP"
        ]
        
        self.shell.load_from_string(program_lines)
        
        initial_count = len(self.shell.executor._program)
        
        # Renumber
        self.shell.cmd_renum(None, False)
        
        final_count = len(self.shell.executor._program)
        self.assertEqual(initial_count, final_count, 
                        f"Complex program line count should not change: expected {initial_count}, got {final_count}")
        
        # Check that all original content is preserved
        program_text = []
        for line in self.shell.executor._program:
            statements = []
            for stmt in line.stmts:
                statements.append(str(stmt))
            program_text.append(f"{line.line} {' : '.join(statements)}")
        
        # Verify key content is preserved
        full_text = " ".join(program_text)
        self.assertIn("check limits on for loops", full_text, "REM statement should be preserved")
        self.assertIn("FIRST ERROR", full_text, "Error message should be preserved")
        self.assertIn("AFTER LOOP 2", full_text, "Print statement should be preserved")
        
        # Count STOP statements - should be exactly 2 (one in IF THEN, one at the end)
        stop_count = sum(line.count("STOP") for line in program_text)
        self.assertEqual(stop_count, 2, f"Should have exactly 2 STOP statements, found {stop_count}")

    def test_renumber_preserves_line_references(self):
        """Test that GOTO and GOSUB references are properly updated"""
        program_lines = [
            "100 GOTO 300",
            "200 PRINT \"SKIP ME\"",
            "300 PRINT \"TARGET\"",
            "400 END"
        ]
        
        self.shell.load_from_string(program_lines)
        
        # Renumber
        self.shell.cmd_renum(None, False)
        
        # Check that GOTO reference was updated
        program_text = []
        for line in self.shell.executor._program:
            statements = []
            for stmt in line.stmts:
                statements.append(str(stmt))
            program_text.append(f"{line.line} {' : '.join(statements)}")
        
        # The GOTO should now point to the renumbered line
        self.assertTrue(any("GOTO 120" in line for line in program_text), 
                       f"GOTO should be updated to new line number: {program_text}")

    def test_renumber_control_flow_statements(self):
        """Test that all control flow statements renumber correctly and no lines are dropped"""
        
        # Create a test program with all types of control flow statements
        test_program = [
            "100 REM Test program for renumbering control flow",
            "110 LET X = 1",
            "120 GOTO 200",
            "130 GOSUB 300",
            "140 ON X GOTO 200,300",
            "150 ON X GOSUB 200,300",
            "160 GOTO X OF 200,300",
            "170 GOSUB X OF 200,300",
            "180 RESTORE 200",
            "190 IF X=1 THEN 200",
            "200 LET Y = 2",
            "210 RETURN",
            "300 LET Z = 3",
            "310 RETURN",
            "999 END"
        ]
        
        shell = BasicShell()
        shell.load_from_string("\\n".join(test_program))
        original_program = shell.executor._program
        self.assertEqual(len(original_program), 15, "Original program should have 15 lines")
        
        # Renumber the program
        shell.cmd_renum("1000 10", verbose=False)
        renumbered_program = shell.executor._program
        self.assertEqual(len(renumbered_program), 15, "Renumbered program should still have 15 lines")
        
        # Create a dictionary of renumbered lines for easy lookup
        renumbered_lines = {line.line: line.source for line in renumbered_program}
        
        # Expected line mapping:
        # 100->1000, 110->1010, 120->1020, 130->1030, 140->1040, 150->1050, 160->1060, 170->1070, 
        # 180->1080, 190->1090, 200->1100, 210->1110, 300->1120, 310->1130, 999->1140
        
        # Verify target lines exist
        self.assertIn(1100, renumbered_lines, "Target line 200->1100 should exist")
        self.assertIn(1120, renumbered_lines, "Target line 300->1120 should exist")
        
        # Verify target lines have correct content
        self.assertIn("LET Y=2", renumbered_lines[1100], "Line 1100 should contain 'LET Y=2'")
        self.assertIn("LET Z=3", renumbered_lines[1120], "Line 1120 should contain 'LET Z=3'")
        
        # Check specific control flow renumbering
        test_cases = [
            # (expected_line, expected_content_pattern, description)
            (1020, "GOTO 1100", "Simple GOTO should point to renumbered line 200->1100"),
            (1030, "GOSUB 1120", "Simple GOSUB should point to renumbered line 300->1120"), 
            (1040, "ON X GOTO 1100,1120", "ON...GOTO should point to renumbered lines"),
            (1050, "ON X GOSUB 1100,1120", "ON...GOSUB should point to renumbered lines"),
            (1060, "GOTO X OF 1100,1120", "Computed GOTO should point to renumbered lines"),
            (1070, "GOSUB X OF 1100,1120", "Computed GOSUB should point to renumbered lines"),
            (1080, "RESTORE 1100", "RESTORE should point to renumbered line 200->1100"),
            (1090, "IF X=1 THEN GOTO 1100", "IF THEN should point to renumbered line 200->1100"),
        ]
        
        for expected_line, expected_pattern, description in test_cases:
            self.assertIn(expected_line, renumbered_lines, f"{description} - line {expected_line} missing")
            actual_content = renumbered_lines[expected_line]
            self.assertIn(expected_pattern, actual_content,
                         f"Line {expected_line} content wrong.\\nExpected: {expected_pattern}\\nActual: {actual_content}\\n{description}")

    def test_renumber_preserves_all_lines(self):
        """Test that renumbering doesn't drop any lines from a complex program"""
        # ... existing code ...


if __name__ == '__main__':
    unittest.main()
