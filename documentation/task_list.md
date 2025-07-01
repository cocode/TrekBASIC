# Task List

### Else
I don't believe that two ELSEs on one line work.

### stmts command
The 'stmts' command prints an extra : before the goto on something simple like "100 if x=1 then goto 100"

### READ vs INPUT
Looks like Dartmouth basic uses READ instead of INPUT. We could add that without conflict. If the semantics are the
same, we could just alias.

### Escaped quotes
Should I support \" in Strings? I don't recall older basics doing that.

### Benchmark timing for llvm code.
Don't want to count startup time.

# ValueError
In basic loading. I think it's been rethrown twice.
And has the wrong line number. (file line)

# When single stepping in basic_shell, the list
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

### Support more built-in functions: LOG10. We can now add more functions easily in basic_functions.py
Do this on an as-needed basis, don't just throw everything in.

### Warn on Exit if Edited
Now that we can add/replace lines in the shell, we should warn before exiting, if the program was modified.

### Support "OPTION BASE"
Add OPTION BASE statement to set the starting index of array variables as either 0 or 1
Found in GWBASIC
