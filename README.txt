This is going to be my attempt to port the original "star trek" game, in basic, to python.

https://en.wikipedia.org/wiki/Star_Trek_(1971_video_game)

There are several versions available.

startrek.bas: http://www.bobsoremweb.com/startrek.html
supertrek: http://www.vintage-basic.net/bcg/superstartrek.bas

Two options:
1. Port the code
2. Write a basic interpreter

2 sounds like more fun

TODO on interpreter.
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
   fix all assertraises to use "with" style