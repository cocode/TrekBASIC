# Known Issues
See also future.md

1. Support different BASIC dialects. 
   
   Currently, TrekBasic only supports one dialect, the one that runs 
   programs/superstartrek.bas. 
   
   This document describes the compatibility issues between various versions of BASIC: 
    https://files.eric.ed.gov/fulltext/ED083819.pdf
   
   basic_dialect.py has some configuration options,
   but that approach limits you to supporting only one dialect without
   making code changes. basic_dialects should probably be replaced with 
   a config file (json? YAML?) that could be read at run time, so you could 
   have a config file for each dialect.
   
   Auto-detecting versions of basic would be great, but might not be feasible.
   1. Support more built-in functions: LOG10. Can now add more functions easily in basic_functions.py 
   1. Need to support "ELSE" for superstartrek3.bas
   1. Some versions of basic allowed a single quote for REM. Should add this.
   2. I'm going to note here: on multi-statement lines, with an IF/THEN, if the condition is false, then 
   we go to the next LINE, not the next statement on the IF / THEN line. 
      3. 100 I = 0: J = 0: K = 0
      4. 200 if 1 = 0 then I = 1: J = 2: K = 3
      5. 300 PRINT K
   6. will print 3
   7. obviouslyl, if a=b then 200: k=4
   8. should never execute the statement k=4

1. TrekBot Improvements
   
   TrekBot is an automated program to play Star Trek, that was build to help with code coverage testing. It's not very
   skilled at this point. It usually dies, and doesn't get very high coverage, yet.
   There are two versions, one random one, that always dies soon, and a CheatBot that does a bit better,
   by cheating.
   1. What uses star dates? Am I wasting star dates in TrekBot by setting the shields all 
   the time?
   1. check k9(count of Klingons alive)  at end, to see if trek bot won

1. Performance Testing
   
   You can do performance testing with cProfile and gprof2dot.py. 
   I don't have dot installed, I just found an online version, and used that. 
    python -m cProfile  -s tottime trek_bot.py 
    python venv/lib/python3.9/site-packages/gprof2dot.py -f pstats test.pstats

1. COMMAND ISSUES
   2. is there really not a "clear workspace" command?
   3. does list really not work on an empty workspace?
   4. load command should accept quotes
   5. Support lower case commands.print as well as PRINT
1. Debugging Improvements
    1. Desperately need "step over" vs "step into" for debugging.
    1. Add "trace on" and "trace off" statements to the language, to control writing of the trace file.
    1. Having trace_file as a parameter to the constructor, but not using it until run_program makes no sense.
    1. Need to flush the trace file periodically. maybe every line. Otherwise it gets lost when we crash.
    1. Should remove REM statements from code coverage, many of them are unreachable
    1. Can I re-raise exceptions differently, so I don't lose
stack information for the original exception?
1. Parsing/Lexing issues.
   1. BASIC is an ugly language, which is not designed for easy parsing.
      Newer dialects of BASIC are better, but TrekBASIC supports syntax like:

       "IFX>YANDX<ZTHEN100"

    1. All expressions should be lexed at parse time. Most are, but not all.
    1. Maybe move the operators enum to it's own file, so  it has no dependencies, and then use a dict
for the mapping.
    1. could also move the lexing to basic_parsing, and then basic_openators.py wouldn't need the lexer
    1. Operator eval functions need to return the correct type, not just always "num". Start by returning the type passed in
1. Testing Improvements
   1. Write smaller test programs.
    1. Split tests
        1. tests of basic (integration). These should not be implementation independent.
        1. tests of internal functions. Unit tests.
1. Renumber
    1. Now working. 
    1. Run a trace of star strek, before and after renumbering, for verificaion.
1. TODO Search and destroy for literal strings used for what should be enums.
1. You know, maybe I don't need to pass the symbol_type everywhere. You can tell the type of a variable
   from its name. FNx = function, $ == string, I guess you still have to know array vs. not.
1. Need to clarify when BASIC would keep a number as an int vs. a float.
1. Should add parsing of all variables, so I can find references to a variable. 
    1.  Could do this in parse tree.


## Bugs in the BASIC program (superstartrek.bas):

### Infinite Recursion on Error
When trek_bot continuously gave a command of "SHE", when "SHIELD CONTROL INOPERABLE",
I eventually hit
Syntax Error in line 2080: SyntaxError: FORs nested too deeply: 2080 FORI=1TO9:IFLEFT$(A$,3)<>MID$(A1$,3*I-2,3)THEN2160
This looks to be a bug in the original basic, that would never matter, as
a human wouldn't give an error response 2000 times.
Current state is:  CheatState.SHIELDS

### Division by Zero
1. TrekBot may have found a bug in superstartrek.bas: Syntax Error in line 8330: Division by zero: 8330 PRINT"DIRECTION =";C1+(ABS(A)/ABS(X)):GOTO8460

maybe course is 1 <= course <= 9. 9 appears to be the same as one, 0 is not 
accepted.
<< NAV
>> COURSE (0-9)
<< 0
>>>    LT. SULU REPORTS, 'INCORRECT COURSE DATA, SIR!'
>> COMMAND