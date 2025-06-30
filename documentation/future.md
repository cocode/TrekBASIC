# Future

## Targets
By using python and LLVM, we can run TrekBasic almost anywhere. 

We'd like to run in the browser, as some point. While I see no particular need for using basic to script web applications, but 
the idea amuses me. 

## Dialects
There are so many dialects of basic, with not just minor differences, like the name of a function,
but complete changes like not requiring line numbers, or supporting multiple-character
variable names. Things that you can't just extend one interpreter to support both, since they
are fundamentally incompatible.

### Pluggable
The way to support this is to have multiple parsers. I don't know of a case yet where we will
need pluggable backends. We do have some switches, like "arrays start at 1 or 0".   basic_dialect.py has some configuration options,
 
Currently, TrekBasic only supports one dialect, the one that runs 
programs/superstartrek.bas. It has a few added non-conflicting features, like allowing
"#" for not equals, in addition to "<>", so it can run hunt_the_wumpus.
 
   This document describes the compatibility issues between various versions of BASIC: 
    https://files.eric.ed.gov/fulltext/ED083819.pdf
   
   
   Auto-detecting versions of basic would be great, but might not be feasible.
   1. Support more built-in functions: LOG10. Can now add more functions easily in basic_functions.py 
   2. I'm going to note here: on multi-statement lines, with an IF/THEN, if the condition is false, then 
   we go to the next LINE, not the next statement on the IF / THEN line. 
      3. 100 I = 0: J = 0: K = 0
      4. 200 if 1 = 0 then I = 1: J = 2: K = 3
      5. 300 PRINT K
   6. will print 3
   7. obviouslyl, if a=b then 200: k=4
   8. should never execute the statement k=4

