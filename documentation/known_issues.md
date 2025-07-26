# Known Issues
See also future.md

### DIM

* can't take an expression
* when it throws an exception, it's not properly wrapped.It looks like it gets caught and rethrown twice. Should only be once.



### stmts command
The 'stmts' command prints an extra : before the goto on something simple like "100 if x=1 then goto 100"
### READ vs INPUT
Looks like Dartmouth basic uses READ instead of INPUT. We could add that without conflict. If the semantics are the
same, we could just alias.
### Escaped quotes
Should I support \" in Strings? I don't recall older basics doing that, but some do.

### READ, DATA, RESTORE
need to implement for hunt the wumpus

### TrekBot
   TrekBot is an automated program to play Star Trek, that was build to help with code coverage testing. It's not very
   skilled at this point. It usually dies, and doesn't get very high coverage, yet.
   There are two versions, one random one, that always dies soon, and a CheatBot that does a bit better,
   by cheating. I should add a smart one that just plays the game, fairly
   1. What consumes my star dates? Am I wasting star dates in TrekBot by setting the shields all 
   the time?
   1. check the number of Klingons alive, variable k9, at the end of the game, to see if trek bot won

### Performance Testing
   
   You can do performance testing with cProfile and gprof2dot.py. 
   I don't have dot installed, I just found an online version, and used that. 
    python -m cProfile  -s tottime trek_bot.py 
    python venv/lib/python3.9/site-packages/gprof2dot.py -f pstats test.pstats

### LLVM
1. Compiler issues (LLVM)
   2. Much harder to do dynamic array dimensions in a compiler. 
   3. For now, do all arrays and functions statically.Can we throw an error on redefintions?
   4. this may be a problem, it's a workaround for dynamic reuse of variable names
      5. Scalar/Array variable separation: Arrays can now have both array elements N(1), N(2), N(3) and a scalar variable N simultaneously
6. Runtime issues
   7. At runtime, I should be getting runtime errors, not basicsyntaxerrors
      8. new type created. Needs to be used.

### Debugging Improvements
    1. Desperately need "step over" vs "step into" for debugging.
    1. Add "trace on" and "trace off" statements to the language, to control writing of the trace file.
       2. or maybe trace filename and trace off
    1. Having trace_file as a parameter to the constructor, but not using it until run_program makes no sense.
    1. Need to flush the trace file periodically. maybe every line. Otherwise it gets lost when we crash.
    1. Should remove REM statements from code coverage, many of them are unreachable
    1. Can I re-raise exceptions differently, so I don't lose  stack information for the original exception?

### Parsing
1. Parsing/Lexing issues.
   1. BASIC is an ugly language, which is not designed for easy parsing.
      Newer dialects of BASIC are better, but TrekBASIC supports syntax like:

       "IFX>YANDX<ZTHEN100"

    1. All expressions should be lexed at parse time. Most are, but not all.
    1. Maybe move the operators enum to it's own file, so  it has no dependencies, and then use a dict
for the mapping.
    1. Could also move the lexing to basic_parsing, and then basic_openators.py wouldn't need the lexer
    1. Operator eval functions need to return the correct type, not just always "num". Start by returning the type passed in
1. Testing Improvements
   1. Write smaller test programs.
1. TODO Search and destroy for literal strings used for what should be enums.
1. You know, maybe I don't need to pass the symbol_type everywhere. You can tell the type of a variable
   from its name. FNx = function, $ == string, I guess you still have to know array vs. not.
1. We need to clarify when BASIC would keep a number as an int vs. a float.
1. Should add parsing of all variables, so I can find references to a variable. 
    1.  Could do this in parse tree.


## Bugs in the BASIC program (superstartrek.bas):

# Infinitely Nested FOR loops 
Fixed. SuperStarTrek jumps out of loops and then restarts them. A naive implementation assumes you won't do that
and is "correct" behavior. For now, if the loop we are entering uses the same loop index variable as the one on the top 
of the "for stack", we erase the top entry and add a new one. 
This wouldn't fix doing this with stacking nested loops, like "fori;forj", recursively 1000 times, for that, we'd need to look 
farther down the stack. But that should be quite doable.

### Exponentiation.
Exponentiation is currently left associative, as opposed to the more standard right association. We do this because 
older dialects of basic had it that way, and we are currently emulating older versions.
This could be handled as a dialect option in basic_dialect.py
