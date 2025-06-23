10 REM Test complex expressions
20 A=5
30 B=3
40 C=2
50 D=ABS(-10)*SQR(16)
60 E=(A>B) AND (B>C)
70 F=(A<B) OR (B>C)
80 G=-A+B*C
90 H=LEN("HELLO")+INT(3.7)
100 PRINT "ABS(-10)*SQR(16) ="; D
110 PRINT "(5>3) AND (3>2) ="; E
120 PRINT "(5<3) OR (3>2) ="; F
130 PRINT "-5+3*2 ="; G
140 PRINT "LEN('HELLO')+INT(3.7) ="; H
150 END 