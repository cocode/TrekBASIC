100 REM Test IF THEN
110 A = 5
115 B = 10
116 C = 1
117 REM Simple IF
120 IF A > 0 THEN B = 1
130 IF B <> 1 THEN PRINT "FAIL: Expected B=1, got"; B: STOP
131 REM IF with expression
133 IF A > B - 7 * C THEN B = 1
134 IF B <> 1 THEN PRINT "FAIL: Expected B=1, got"; B: STOP
135 IF A > B - 7 * C THEN B = 1
136 IF B <> 1 THEN PRINT "FAIL: Expected B=1, got"; B: STOP

140 A=5:B=10:C=0
150 IF B = 10 THEN IF A = 5 THEN C=2
160 IF C <> 2  THEN PRINT "FAIL #1: Expected C=2, got"; C: STOP
240 D=0
250 IF B = 10 THEN D=5: IF A = 5 THEN C=2
260 IF C <> 2  THEN PRINT "FAIL #2: Expected C=2, got"; C: STOP
270 IF D <> 5  THEN PRINT "FAIL #3: Expected D=2, got"; D: STOP

