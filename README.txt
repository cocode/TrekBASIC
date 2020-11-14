This is going to be my attempt to port the original "star trek" game, in basic, to python.

https://en.wikipedia.org/wiki/Star_Trek_(1971_video_game)

There are several versions available.

startrek.bas: http://www.bobsoremweb.com/startrek.html
supertrek: http://www.vintage-basic.net/bcg/superstartrek.bas

Two options:
1. Port the code
2. Write a basic interpreter

2 sounds like more fun

Definitions:
A LINE is made up of multiple STATEMENTS, each one beginning with a KEYWORD.
LINE: 100 PRINT X:GOTO 100
STATEMENTS: "PRINT X" and "GOTO 100"
KEYWORDS "PRINT", and "GOTO"

TODO on interpreter.
Use lambda with BINOP to cut the number of OP classes 90%
Is it ok to do some processing at load time? If I do, then some errors may raise their exception
on program load time. Is this a problem? I'll have to change a few tests, if I do, like "if with no then"
0. Need tuples for function calls FNA(x,y,z) and array subscripts A(1,2,3)
    0.0 Note that these subscripts can be expressions.
    1. Current function and array code only works for single, literal values.
1. Should probably split symbol table from executor. It would cut circular references. DONE
2. Expressions will probably be the hardest
    a. Expression evaulation DONE
    b. Expression assignment DONE - mostly,
        c. Array assignment.
    c. Support parens! DONE
    d. Unary minus - Currently causing problems.
3. Built in functions.
    INT, RND - DONE
    currently, we pass symbols in to the Expression, but that means they bypass get_symbol, which
    can hide format changes in the symbol table, like I just made.
4. Convert the program execution to a class.
5. Write smaller test programs.
6. Implement subroutines (GOTO)
7. Implement FOR loops
8. Write "renum" utility. Split all multiline statements, and renumber at increments of 10
   Then reformat the startrek source.

   write exponentiation test 2**3**2
   I THINK DONE fix all assertraises to use "with" style
   DONE  assert_syntax should not take a line. The line is from the executor, and it will catch and add the line
   Should we precompute expressions to ASTs on load?