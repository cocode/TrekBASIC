10 REM Test ON...GOTO and ON...GOSUB statements
20 PRINT "Testing ON...GOTO statement"
30 FOR I = 1 TO 4
40 PRINT "I ="; I; ": ";
50 ON I GOTO 100, 200, 300, 400
60 PRINT "ERROR: Should not reach here"
70 NEXT I
80 GOTO 500
90 REM
100 PRINT "Branch 1 (I=1)": GOTO 70
200 PRINT "Branch 2 (I=2)": GOTO 70
300 PRINT "Branch 3 (I=3)": GOTO 70
400 PRINT "Branch 4 (I=4)": GOTO 70
460 REM
500 PRINT
510 PRINT "Testing ON...GOSUB statement"
520 FOR J = 1 TO 3
530 PRINT "J ="; J; ": ";
540 ON J GOSUB 600, 700, 800
550 PRINT " (returned)"
560 NEXT J
570 GOTO 900
580 REM
600 PRINT "Subroutine 1";: RETURN
700 PRINT "Subroutine 2";: RETURN
800 PRINT "Subroutine 3";: RETURN
850 REM
900 PRINT
910 PRINT "Testing valid range"
920 REM Test with valid indices only
930 PRINT "Testing ON 2 GOTO with 3 targets:"
940 ON 2 GOTO 1000, 1100, 1200
950 PRINT "ERROR: Should not reach here"
960 GOTO 1300
1000 PRINT "ERROR: Should not reach target 1": STOP
1100 PRINT "Reached target 2 correctly": GOTO 1300
1200 PRINT "ERROR: Should not reach target 3": STOP
1300 PRINT "All tests completed successfully"
1310 END 