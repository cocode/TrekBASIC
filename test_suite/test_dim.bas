10 REM CHECK ARRAY USE
90 DIM D(5),K1(7),K2(7),K3(7),S(7,7),Q(7,7)
100 D(5) = 99
110 D(5) = D(5) + 1
200 IF D(5) <> 100 THEN STOP

300 FOR X = 1 TO 7
310 FOR Y = 1 TO 7
320 LET Q(X, Y) = Y + 10 * X
330 NEXT Y
340 NEXT X
350 IF Q(3,4) <> 34 THEN STOP

