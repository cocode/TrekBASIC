10 REM Test multi-statement lines
20 A=1:B=2:C=3
30 PRINT "A="; A; "B="; B; "C="; C
40 IF A=1 THEN PRINT "A is 1":GOTO 60
50 PRINT "Should not reach here"
60 PRINT "Multi-statement line with IF"
70 FOR I=1 TO 3:PRINT I;:NEXT I
80 PRINT
90 END 