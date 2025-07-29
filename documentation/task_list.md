# Task List

### Fix tests.
It looks like @EXPECT_EXIT_CODE=2 is not working in the compiler, so two tests are not passing. Fixed?

### Else
I don't believe that two ELSEs on one line work. Write a test.

### stmts command
The 'stmts' command prints an extra : before the goto on something simple like "100 if x=1 then goto 100"

### format command
Only basic support. *FOR* statement supports format, nothing else does.
Need a format_expression command. Should put spaces around everything.
could we just parse the __str__ output?

### READ vs INPUT
Looks like Dartmouth basic uses READ instead of INPUT. We could add that without conflict. If the semantics are the
same, we could just alias.

### Escaped quotes
Should I support \" in Strings? I don't recall older basics doing that. 
No, I am taking that out, as that's a python convention, not a BASIC convention. 

### Benchmark timing for llvm code.
Don't want to count startup time.

# ValueError
In basic loading. I think it's been rethrown twice.
And has the wrong line number. (file line). How to repreduce?


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
For example: LOG10. We can now add more functions easily in basic_functions.py
Do this on an as-needed basis, don't just throw everything in.

### Warn on Exit if Edited
Now that we can add/replace lines in the shell, we should warn before exiting, if the program was modified.

### Done
Support "OPTION BASE"

Add OPTION BASE statement to set the starting index of array variables as either 0 or 1. Found in GWBASIC. 

We currently support this, and other, OPTION commands in basic_shell.py, but
do not yet allow it in program code. It should be easy to add, but adding that makes that basic 
program incompatible. Maybe we should have config files? if you have basprogram.bas, then 
maybe basprogram.json specifies the dialect?

### Restructure
Move all remaining tests in ./* to approriate test dir or to the test_suite

### Fix all TODOs in the Code

### Make basic.py and tbc.py runnable
Add shebang line. But it still won't be runnable outside of the venv. Maybe use UV?

### Publish to pypi
Package things properly.

### Limits
Put a limit on the size of all dynamic objects, strings, arrays. What else? these should be settable in doskect.py
### Put a limit on the size of all dymnamic objects, strings, arrays. What else?


### Call
Add a call statement, to invoke other basic prograns. This will give us some
modularity, Otherwise everything is global in BASIC. 

### Every reraised exception should have "from e"

### Lexing
It looks like we lex expressions every time we get to them, at least in some cases. We should do it 
once on load.

### Print statements
We are failing two tests. Print using, and tabs, which just aren't supported yet in TrekBasicPy

### Support More Versions of BASIC
We have basic_dialect.py, and swappable lexers. Do we need more?

### Sym command
We should print all Xs on sym X, not require the user to select the type.

## Get rid of asserts
These are fine when developing, but they should now all be exceptions that we handle properly.

## Ambiguity
what does the following mean?
100 LET A=1
112 LET B=2
120 LET C=A=B
125 PRINT A,B,C
130 END

What does that mean?
a) Invalid, as we don't have boolean operators in expression in basic, only in IF / THEN
b) C gets true if A is equal to B 
c) The value of B is put into A, then put into c (A=B;C=A) (DARTHMOUTH?)

currently we are b).

### Benchmarks in Basic
Anything in BASIC is runnable on all versions, and should be moved to the basic_test_suite.

We have a benchmark directory, all of them probably could be used for tests.
