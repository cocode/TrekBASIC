# Frequently Asked Questions (FAQ)

# Can TrekBasic run anything beside SuperStarTrek?

Yes, TrekBasic is a full BASIC implementation — both the interpreted and the compiled versions.

The challenge with running any older BASIC programs is that
there were so many difference versions of BASIC. A program that runs on one version of BASIC likely 
will not run on another version. As an example, some basics don't require spaces:
```100FORA=BTOCSTEPD```
Others required a more relaxed versions
```100 FOR A=B TO C STEP D```

Some versions start arrays at 0, some at 1; some are case-insensitive, and on, and on. 

If you have a particular program you want to run, and it doesn't run, 
it should be relatively easy to adapt TrekBasic to run it. TrekBasicPy provides 
two lexer implementations, one for the no-spaces BASICs and one for the spaced BASIC.

The file trekbasicpy/basic_dialect has settings for uppercasing input (expected in superstartrek.bas), 
array base, and others. You can edit them there, and rerun. There are also commands in 
***trekbasicpy/basic_shell.py*** to change these dynamically.




