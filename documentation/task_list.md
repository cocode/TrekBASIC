# Task List

Don't start working on these, without asking first

### Else
Else is not yet impleted.
### Renumber 
Renumber is not working correctly
### stmts command
The 'stmts' command prints an extra : before the goto on something simple like "100 if x=1 then goto 100"
### READ vs INPUT
Looks like Dartmouth basic uses READ instead of INPUT. We could add that without conflict. If the semantics are the
same, we could just alias.
### Escaped quotes
Should I support \" in Strings? I don't recall older basics doing that, but some do.

### READ, DATA, RESTORE
need to implement for hunt the wumpus

### Benchmark timing for llvm code.
Don't want to count startup time.

### REM 
A REM in the middle of an IF then might cause  problems
we should only allow rem as the first statement on
a line, Google says they can be not the first statement 
in a line. I'm worried that this will complicate our
nested IF then parsing, if we get a REM in a nested IF, how
will it go the end of the lines above it.

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

# REM
We don't tokenize a rem statement in the middle of a line correctly.
1300 I=RND(1):REM IF INP(1)=13 THEN 1300
tokenizes as
1300 LET I=RND(1)|	REM |	THEN|	GOTO 1300|
which is an infinite loop!
It should be
1300 LET I=RND(1)| REM THEN GOTO 1300
