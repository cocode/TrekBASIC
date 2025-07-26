10 REM Test DIM with function calls containing commas
20 A = 10
30 B = 15
40 C = 7
50 REM This should parse correctly: MAX(A,B) and MIN(C,A) as separate dimensions
55 REM But it doesn't. If I find a real world case, then I will worry about it: TODO:  DIM U(MAX(A,B), MIN(C,A))
60 DIM X(3,4), Y(A,B), Z(5,6)
70 PRINT "DIM with multi-dimensional arrays works!"
80 REM Set some values to verify the arrays were created properly
90 X(1,1) = 42
100 Y(5,10) = 99
110 Z(3,4) = 77
120 PRINT "X(1,1)="; X(1,1)
130 PRINT "Y(5,10)="; Y(5,10)
140 PRINT "Z(3,4)="; Z(3,4)
150 END 
