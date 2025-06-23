10 A = 1 AND 1
20 B = 1 AND 0
30 C = 0 AND 1
40 D = 0 AND 0
50 PRINT "A ="; A
60 PRINT "B ="; B
70 PRINT "C ="; C
80 PRINT "D ="; D
90 IF A <> 1 THEN PRINT "A is wrong": STOP
100 IF B <> 0 THEN PRINT "B is wrong": STOP
110 IF C <> 0 THEN PRINT "C is wrong": STOP
120 IF D <> 0 THEN PRINT "D is wrong": STOP
130 PRINT "All AND tests passed!"
140 END 