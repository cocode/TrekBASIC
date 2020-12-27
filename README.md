# TrekBasic
This is a full BASIC interpreter, written in Python.

My goal was to be able to play the old Star Trek game, which was written in BASIC.
https://en.wikipedia.org/wiki/Star_Trek_(1971_video_game)

One challenge is that virtually every version of BASIC is different, 
sometimes substantially, and the available versions of start trek do not
specify which version of basic they were written for. 

This document describes the compatibility issues: 
https://files.eric.ed.gov/fulltext/ED083819.pdf

I considered simply porting Star Trek to Python, but 
writing an interpreter sounded like more fun.

## Versions
There are several versions of Star Trek available.

* startrek.bas: http://www.bobsoremweb.com/startrek.html
* supertrek: http://www.vintage-basic.net/bcg/superstartrek.bas
* https://github.com/RC2014Z80/RC2014/blob/master/BASIC-Programs/Super%20Startrek/startrek.bas
* https://github.com/lwiest/BASICCompiler/blob/master/samples/STARTREK.BAS


## Terminology
A LINE is made up of multiple STATEMENTS, each one beginning with a KEYWORD.

### LINE
    100 PRINT X:GOTO 200
### STATEMENTS
    "PRINT X" and "GOTO 100"
### KEYWORDS
    "PRINT", and "GOTO"

## TODO on interpreter

1. Should have a simple "save" that checks saving from the parsed version
   with no renumber.
   1. Now have "format" command in basic_shell.py
1. It could be fun to write Wasm Basic. (See "wasm.txt"). Options
    1. Write interpreter that generates "B-code."
    1. Options to execute in browser
        1. Generate wasm from b-code (this is best) 
        1. Or could write  b-code interpreter.
        1. Or could find someone else's basic written in a languages 
    that compiles to wasm
    1. there's a gw-basic clone. maybe generate code from its parse tree.
1. In progress: Writing a smarter player strategy, so I can code 
   cover the "win" part of the code. The random player always loses.
1. What uses star dates? Am I wasting life by setting the shields all 
   the time?
1. Performance testing with cProfile and gprof2dot.py. I don't have":
dot installed, I just found an online version, and used that. 
    python -m cProfile  -s tottime trek_bot.py 
    python venv/lib/python3.9/site-packages/gprof2dot.py -f pstats test.pstats
1. Having trace_file as a parameter to the constructor, but not using it until run_program makes no sense.
1. remove REM from code coverage, many of the are unreachable
1. check k9(count of Klingons alive)  at end, to see if trek bot won
1. Need to support "ELSE" for superstartrek3.bas
1. It should be possible to save code coverage data across multiple runs,
   so I can get to 100% coverage.
    1. Should have better formatting to tell what lines I still need to execute.
1. Can I re-raise exceptions differently, so I don't lose
stack information for the original exception?
1. Add support for automatically understanding new two-character operators.
    FIX lexer.
1. Support dialects. At least for the four star trek programs I have. (basic_dialects.py)
    Cool thought: Auto-detect dialects?
1. Now have a parsed statement for all statement types.
    1. All expressions should be lexed at parse time, but are not yet.
    1. Let statements do this, but I think ON...GOSUB and others don't, yet.
1.  Should we precompute expressions to ASTs on load? - Yes, but not done yet.
1. More built in functions: EXP, LOG10. (have LOG) 
1. Write smaller test programs.
1. Split tests
    1. tests of basic (integration). These should be implementation independent.
    1. tests of internal functions. Unit tests.
1. Write "renum" utility. Split all multiline statements, and renumber at increments of 10
    1. Then reformat the startrek source.
    1. Run a trace of star strek, befre and after for verificaion.
1. Fix functions to store their extra into in the symbol table, not in the "op" parameter.
    1. store data in symbol table
    2. Use it
    3. remove old versions.
    4. Hmm. Looks like the issues is not the symbol table, its that the expression evaluator doesn't
        pass that information into FUNC_MONO_OP
1. TODO Fix the lexer to allow all two character operators, and to require no changes if more are added.
1.     TODO Replace namedtuple for ste with dataclass (maybe)
1.     TODO Search and destroy for literal strings used for what should be enums.
1. Maybe move the operators enum to it's own file, so  it has no dependencies, and then use a dict
for the mapping.
1. could also move the lexing to parsed_statements, and then basic_openators.py wouldn't need the lexer
1. Operator eval functions need to return the correct type, not just always "num". Start by returning the type passed in
1. Maybe write trace to a file. With the variables on that line. Or build a debugger. Debugger built.
    X=3, Y=4
    100 IFX+Y>3THENPRINT"FOO"
1. Add "trace on" and "trace off" statements to the language, to control writing of the trace file.
1. Need to flush the trace file periodically. maybe every line.
1. Maybe add "run" vs. "continue" for the debugging. Have single step now.
1. You know, maybe I don't need to pass the symbol_type everywhere. You can tell the type of a variable
   from its name. FNx = function, $ == string, I guess you still have to know array vs. not.
1. Desperately need step over vs step into for debugging.
1. Need to clarify when BASIC would keep a number as an int vs. a float.
1. Should add parsing of all line numbers used in a line, so I can renumber
1. Should add parsing of all variables, so I can search references.
    1.  Could do this in parse tree.
1. Some versions of basic allowed a single quote for REM
1. load in basic shell doesn't reload a changed program (Can't reproduce. Maybe forgot to save?)
## References
1. https://madexp.com/wp-content/uploads/2018/02/Microsoft_Basic_8086Xenix_Reference.pdf
2. http://www.classiccmp.org/cini/pdf/Apple/AppleSoft%20II%20Basic%20Programming%20Manual.PDF
1. TrekBot may have found a bug in superstartrek.bas: Syntax Error in line 8330: Division by zero: 8330 PRINT"DIRECTION =";C1+(ABS(A)/ABS(X)):GOTO8460
1. BNF 
    1. https://henry416.wordpress.com/tag/bnf/
    1. https://rosettacode.org/wiki/BNF_Grammar#BASIC
1. https://robhagemans.github.io/pcbasic/
    1. https://robhagemans.github.io/pcbasic/doc/2.0/PC-BASIC_documentation.pdf

## Bugs in the BASIC program (superstartrek.bas):
When trek_bot continuously gave a command of "SHE", when "SHIELD CONTROL INOPERABLE",
I eventually hit
Syntax Error in line 2080: SyntaxError: FORs nested too deeply: 2080 FORI=1TO9:IFLEFT$(A$,3)<>MID$(A1$,3*I-2,3)THEN2160
This looks to be a bug in the original basic, that would never matter, as
a human wouldn't give an error response 2000 times.
Current state is:  CheatState.SHIELDS

maybe course is 1 <= course <= 9 or <10
<< NAV
>> COURSE (0-9)
<< 0
>>>    LT. SULU REPORTS, 'INCORRECT COURSE DATA, SIR!'
>> COMMAND