1000 REM This test a workaround for a bug in the superstartrek program, and possibly others
1010 REM SST exits a FOR loop, via GOTO then comes back and starts the FOR loop from the top
1020 REM This leads to FOR stack overflow eventually, in a good implementation of FOR stack
1030 REM To prevent overflow, but not break other programs, I'm going to check when I start
1040 REM a new loop, and if the top of the stack is the same variable, I'll pop off that
1050 REM FOR loop and push the new one. So, you can only have one loop with the same index running
1060 REM Not, this ignores the case where you effectively do FOR J, FOR K, FOR J. I'm not sure
1070 REM what to do in this case. Pop down until I get the lower J on the stack, so K goes away?
1080 REM Should also check that you can't do two NEXT J - but that needs another file, since
1090 REM the expected outcome is an error

1100 REM Do the loop more than 1000 times, since that's the FOR stack limit.
1101 I = 0
1105 FOR J = 1 TO 10
1120 I = I + 1
1121 REM If we can do this more than 1000 times, then the fix is working.
1130 IF I > 1100 THEN END
1135 GOTO 1105
1140 NEXT J
1150 REM We should never get here, so return an error if we do.
1160 STOP




