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
1. Expressions will probably be the hardest
    a. Expression evaulation DONE
    b. Expression assignment DONE - mostly,
        c. Array assignment.
    c. Support parens!
    d. Unary minus
2. Built in functions.
    INT, RND
    currently, we pass symbols in to the Expression, but that means they bypass get_symbol, which
    can hide format changes in the symbol table, like I just made.
2. Convert the program execution to a class.
3. Write smaller test programs.
4. Implement functions (RAND)
5. Implement subroutines (GOSUB)