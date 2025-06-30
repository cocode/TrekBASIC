100 REM Test IF THEN ELSE functionality
110 A = 5
120 IF A > 0 THEN B = 1 ELSE B = 2
130 IF B <> 1 THEN PRINT "FAIL: Expected B=1, got"; B: STOP
140 IF A < 0 THEN C = 1 ELSE C = 2
150 IF C <> 2 THEN PRINT "FAIL: Expected C=2, got"; C: STOP
160 REM Test string confusion
170 IF A = 5 THEN D$ = "ELSE" ELSE D$ = "THEN"
180 IF D$ <> "ELSE" THEN PRINT "FAIL: Expected D$=ELSE, got "; D$: STOP
190 REM Test multiple statements
200 IF A > 0 THEN E = 10 : F = 20 ELSE E = 30 : F = 40
210 IF E <> 10 THEN PRINT "FAIL: Expected E=10, got"; E: STOP
220 IF F <> 20 THEN PRINT "FAIL: Expected F=20, got"; F: STOP
230 PRINT "IF THEN ELSE tests passed"
240 END 
