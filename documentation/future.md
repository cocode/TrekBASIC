# Future

It would be interesting to make BASIC available in more places, such as web
assembly. 



LLVM could be used to generate code for multiple backends, including wasm.
I see no particular need for using basic to script web applications, but 
the idea amuses me. 

Using LLVM to build a compiler would provide much better
performance. Not that anyone uses BASIC to get high performance. 

It would be nice to have pluggable parsers. 
Every old basic had a slightly different syntax, 
and you can't support more than a few, because eventually they 
conflict. Ideally, you would just plug in a grammar,
and it would work. This only works if it's only
a syntactic different, not a semantic.

### Dialocts
Support different BASIC dialects. 
   
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

