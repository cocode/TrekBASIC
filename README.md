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
    100 PRINT X:GOTO 100
### STATEMENTS
    "PRINT X" and "GOTO 100"
### KEYWORDS
    "PRINT", and "GOTO"

## TODO on interpreter

1. Use ControlLocation for the current instrcution record in Executor
0. Add support for automatically understanding new two-character operators.
    FIX lexer.
1. Fully support N-dimensional arrays. Two-dimensionsal is are working, but might want cleanup.
2. Support dialects. At least the two star trek programs I have. (basic_dialects.py)
3. Starting to parse some statements (like FOR) at load time. Should lex any expressions at load time.
   Should we precompute expressions to ASTs on load? - Yes, but not done yet.
3. Boolean expressions?
4. built in functions: ABS SGN SQR EXP LOG LOG10
6. Convert the program execution to a class.
7. Write smaller test programs.
11. Split tests, tests of basic, vs. tests of internal functions.
9. Write "renum" utility. Split all multiline statements, and renumber at increments of 10
   Then reformat the startrek source.
12. Rename OP classes in basic operations to not be all upppercase.
14. Split stmts out of basic_interpreter.py
    A. One for Executor, One for Statements, one for printing.
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
1. could also move the lexing to parsed_ststements, and then basicopenarots wouldn;t ned the lexer
1. Functions should get an arg with type "array", not "num". which means comma should return "array"
1. Operator eval functions need to return the correct type, not just always "num". Start by returning the type passed in
1. Maybe write trace to a file. With the variables on that line. Or build a debugger.
    X=3, Y=4
    100 IFX+Y>3THENPRINT"FOO"

1. Add "trace on" and "trace off" statements to the language, to control writing of the trace file.
1. Need to flush the trace file periodically. maybe every line.
1. Maybe add "run" vs. "continue" for the debugging.
1. make a run() function, and have "End program" and 'breakpoint' be different flags
Desperately need step over vs step into

## References
1. https://madexp.com/wp-content/uploads/2018/02/Microsoft_Basic_8086Xenix_Reference.pdf
2. http://www.classiccmp.org/cini/pdf/Apple/AppleSoft%20II%20Basic%20Programming%20Manual.PDF

## Known Issues
Syntax Error in line 2290: SyntaxError: Undefined variable: 'C': 2290 IF C$>="a" AND C$<="z" THEN X$=X$+CHR$(ASC(C$)-32) ELSE X$=X$+C$
Useful manual: https://files.eric.ed.gov/fulltext/ED083819.pdf
According to that, and a vague memory, arrays can have the same name as normal variables.
Syntax Error in line 4060: SyntaxError: Can't subscript non-array N of type SymbolType.VARIABLE: 4060 FORI=Q1-1TOQ1+1:N(1)=-1:N(2)=-2:N(3)=-3:FORJ=Q2-1TOQ2+1

