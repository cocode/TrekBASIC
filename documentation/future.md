# Future

## Targets
By using python and LLVM, we can run TrekBasic almost anywhere. 

We'd like to run in the browser, as some point. While I see no particular need for using basic to script web applications, but 
the idea amuses me. 


It would be nice to have pluggable parsers. 
Every old basic had a slightly different syntax, 
and you can't support more than a few, because eventually they 
conflict. Ideally, you would just plug in a grammar,
and it would work. This only works if it's only
a syntactic different, not a semantic.

### Dialects
Support different BASIC dialects. 
   
   Currently, TrekBasic only supports one dialect, the one that runs 
   programs/superstartrek.bas. It 
   
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

### Features
Add a watch commmand, so someone can edit in the editor of their choice, and TrekBasic will reload it automatically.
recommended:  watchdog library 