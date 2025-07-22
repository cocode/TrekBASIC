# Task List

### Fix tests.
We combined test suites, so now that are some tests that aren't passing, as TrekBasic doesn't suport the new
features yet. 
DIM(expr) and Print Using, Tab(), and  test_array_access.bas for LLVM only.

### Else
I don't believe that two ELSEs on one line work.

### stmts command
The 'stmts' command prints an extra : before the goto on something simple like "100 if x=1 then goto 100"

### format command
Only basic support. For statement supports format, nothing else does.
Need a format_expression command. Should put spaces around everything.
could we just parse the __str__ output?
### READ vs INPUT
Looks like Dartmouth basic uses READ instead of INPUT. We could add that without conflict. If the semantics are the
same, we could just alias.

### Escaped quotes
Should I support \" in Strings? I don't recall older basics doing that. 
No, I taking that out, as that's a python convention, not a BASIC convention. 

### Benchmark timing for llvm code.
Don't want to count startup time.

# ValueError
In basic loading. I think it's been rethrown twice.
And has the wrong line number. (file line)

# Done. 
When single stepping in basic_shell, the list
command should indicate the next instruction
with a "*" or something

# Fix Parsing
We partially fixed parsing with inserting colons to force 
statement boundaries, but the real answer is a proper pull parser.
That will fix the rem issue, below, as well.

### Features
Add a watch commmand, so someone can edit in the editor of their choice, and TrekBasic will reload it automatically.
recommended:  watchdog library

### Fix unusual object initialization in renumber methods
- [ ] Replace `object.__new__()` pattern in `ParsedStatementGo.renumber()` and `ParsedStatementOnGoto.renumber()`
- Current code uses `object.__new__(ParsedStatementGo)` to bypass constructor during renumbering
- Better alternatives:
  - Add factory method like `from_renumber()`
  - Add `skip_parsing` flag to constructor
  - Use `copy.deepcopy()` and modify attributes
- Files affected: `basic_parsing.py` lines ~230 and ~280 

### Support more built-in functions
fir example: LOG10. We can now add more functions easily in basic_functions.py
Do this on an as-needed basis, don't just throw everything in.

### Warn on Exit if Edited
Now that we can add/replace lines in the shell, we should warn before exiting, if the program was modified.

### Done
Support "OPTION BASE"
Add OPTION BASE statement to set the starting index of array variables as either 0 or 1
Found in GWBASIC

### Refactor Program
Convert the list[ProgramLine] to a "Program" class. Done. 


### Fix This
COMMAND ^DTraceback (most recent call last):
  File "/Users/tomhill/PycharmProjects/TrekBasic/basic_interpreter.py", line 152, in run_program
    execution_function(self, s)
    ~~~~~~~~~~~~~~~~~~^^^^^^^^^
  File "/Users/tomhill/PycharmProjects/TrekBasic/basic_statements.py", line 250, in stmt_input
    result = executor.do_input()
  File "/Users/tomhill/PycharmProjects/TrekBasic/basic_interpreter.py", line 454, in do_input
    response = input()
EOFError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/tomhill/PycharmProjects/TrekBasic/basic_shell.py", line 861, in <module>
    debugger.do_command()
    ~~~~~~~~~~~~~~~~~~~^^
  File "/Users/tomhill/PycharmProjects/TrekBasic/basic_shell.py", line 852, in do_command
    function(self, args)
    ~~~~~~~~^^^^^^^^^^^^
  File "/Users/tomhill/PycharmProjects/TrekBasic/basic_shell.py", line 434, in cmd_run
    self.cmd_continue(None)
    ~~~~~~~~~~~~~~~~~^^^^^^
  File "/Users/tomhill/PycharmProjects/TrekBasic/basic_shell.py", line 404, in cmd_continue
    rc = self.executor.run_program(self._breakpoints, self._data_breakpoints, single_step=single_step)
  File "/Users/tomhill/PycharmProjects/TrekBasic/basic_interpreter.py", line 164, in run_program
    raise BasicInternalError(F"Internal error in line {current.line}: {e}")
basic_types.BasicInternalError: Internal error in line 1000:

### Restructure
Move all basic.*py files to subdirectory
Move all remaining tests in ./* to approriate test dir

### Fix all TODOs

### Make basic.py and tbc.py runnable
Add shebang line. But it still won't be runnable outside of the venv.

### Publish to pypi

### Limits
Put a limit on the size of all dynamic objects, strings, arrays. What else? these should be settable in doskect.py

### Call
Add a call statement, to invoke other basic prograns. This will give us some
modularity, Otherwise everything is global in BASIC. 

### Put a limit on the size of all dymnamic objects, strings, arrays. What else?

### Every rethrown exception should have "from e"

### test_suite
Test suite is now a standalone project, but we still point to our local copy. We need to merge
all the individual tests suites in TrekBasic, TrekBasicJ BasicRS into the test suite project.

### Lexing
It looks like we lex expression every time we get to them. We should do it on load. 

### PRINT statements 
I think print statments in BasicRS support , in addition to ; to join outputs, and TrekBasic doesn't.
Need to pick one. 

### Print statements
We are failing two tests. Print using, and tabs, which just aren't supported yet.

### Lexing modern Basic
We currently parse the star trek version of basic and that means "FORI=ATOBSTEPC" is valid,

More modern syntax requires spaces or word boundaries. So, FORI is bad, but "I=3"

### Sym command
We should print all Xs on sym X, not require the user to select the type.

# get rid of asserts
These are fine when developing, but they should now all be exceptions that we handle properly.