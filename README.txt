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
0. Support dialects. At least the two star trek programs I have.
1. Starting to parse some statements (like FOR) at load time. Should lex any expressions at load time.
2. Need tuples for function calls FNA(x,y,z) and array subscripts A(1,2,3)
    0.0 Note that these subscripts can be expressions.
    1. Current function and array code only works for single, literal values.
3. Boolean expressions?
4. built in functions: ABS SGN SQR EXP LOG LOG10
5. String functions, like LEFT, LEN, etc.
6. Convert the program execution to a class.
7. Write smaller test programs.
8. Implement FOR loops
9. Write "renum" utility. Split all multiline statements, and renumber at increments of 10
   Then reformat the startrek source.
10. Write a command line shell, like we used to have with load and run (no editor, though), and maybe breakpoints
   Should we precompute expressions to ASTs on load? - Yes, but not done yet.

   It would be nice to have a BASIC command line environment.
    LOAD, RUN, BREAKPOINT
    Implement >= and <= and !=? How does basic do != ? Maybe <>

    TODO Fix functions to store their extra into in the symbol table, not in the "op" parameter.
        1. store data in symbol table
        2. Use it
        3. remove old versions.
        4. Hmm. Looks like the issues is not the symbol table, its that the expression evaluator doesn't
        pass that information into FUNC_MONO_OP
    TODO Fix the lexer to allow all two character operators, and to require no changes if more are added.
    TODO Replace namedtuple for ste with dataclass (maybe)
    TODO Search and destroy for literal strings used for what should be enums.
    TODO what does get_additional do?
