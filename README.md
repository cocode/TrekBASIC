# TrekBasic
TrekBASIC is a full BASIC interpreter, written in Python.

My goal was to be able to play the old Star Trek game, which was written in BASIC.

    https://en.wikipedia.org/wiki/Star_Trek_(1971_video_game). 

I have achieved that goal.



I considered simply porting Star Trek to Python, but 
writing an interpreter sounded like more fun.

## Versions
There are several versions of Star Trek available. 

TrekBASIC currently
runs only programs/superstartrek.bas.

* supertrek: http://www.vintage-basic.net/bcg/superstartrek.bas

### Other Versions
* startrek.bas: http://www.bobsoremweb.com/startrek.html
* https://github.com/RC2014Z80/RC2014/blob/master/BASIC-Programs/Super%20Startrek/startrek.bas
* https://github.com/lwiest/BASICCompiler/blob/master/samples/STARTREK.BAS

## Features

TrekBASIC actually provides a full basic development environment which has:
* Code breakpoints 
* Data write breakpoints 
* Single stepping
* Execution timing 
* Execution tracing
* Code coverage reports
* Reformatting
* Renumbering

# Profiling
You can profile the code using python profilers. 

I have used cProfile and gprof2dot.py. You'll need to install gprof2dot.py 
I don't have dot installed, I just found an online version, and used that. 

    python -m cProfile  -s tottime trek_bot.py 
    python venv/lib/python3.9/site-packages/gprof2dot.py -f pstats test.pstats

## Getting Started
See the documentation directory for more information.

TrekBasic requires python 3

    python basic.py programs/superstartrek.bas

*HINT* If you don't put your shields up, the first hit will kill you! :-)

If you want the development environment, similar to what you would have had with a command line BASIC

    python basic_shell.py

Use "help" to get available commands, like "load programs/superstartrek.abs" and "run". 

I have not implemented an editor in basic_shell. While the old-style line-by-line editing might be nostalgic,
modern editors are *so* much better. 


## Terminology
A LINE is made up of multiple STATEMENTS, each one beginning with a KEYWORD.

### LINE
    100 PRINT X:GOTO 200
### STATEMENTS
    "PRINT X" and "GOTO 100"
### KEYWORDS
    "PRINT", and "GOTO"

