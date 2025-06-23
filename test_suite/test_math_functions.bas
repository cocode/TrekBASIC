10 REM Test math functions with checks
20 A=SIN(0)
30 B=COS(0)
40 C=SQR(16)
50 D=EXP(1)
60 E=LOG(2.718)
70 F=ABS(-5)
80 IF A <> 0 THEN PRINT "FAIL: SIN(0) expected 0, got"; A: STOP
90 IF B <> 1 THEN PRINT "FAIL: COS(0) expected 1, got"; B: STOP
100 IF C <> 4 THEN PRINT "FAIL: SQR(16) expected 4, got"; C: STOP
110 IF ABS(D-2.718) > 0.001 THEN PRINT "FAIL: EXP(1) expected ~2.718, got"; D: STOP
120 IF ABS(E-1) > 0.001 THEN PRINT "FAIL: LOG(2.718) expected ~1, got"; E: STOP
130 IF F <> 5 THEN PRINT "FAIL: ABS(-5) expected 5, got"; F: STOP
140 PRINT "SIN(0) ="; A
150 PRINT "COS(0) ="; B
160 PRINT "SQR(16) ="; C
170 PRINT "EXP(1) ="; D
180 PRINT "LOG(2.718) ="; E
190 PRINT "ABS(-5) ="; F
200 PRINT "All math function tests passed!"
210 END 