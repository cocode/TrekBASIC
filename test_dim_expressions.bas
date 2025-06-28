10 REM Test DIM with expressions and function calls
20 X = 5
30 Y = 3
40 REM Test basic expressions in DIM
50 DIM A(X), B(X+Y), C(X*2)
60 REM Test function calls with commas in DIM
70 DIM D(ABS(-7)), E(SGN(X)), F(INT(3.14))
80 PRINT "DIM with expressions and function calls works!"
90 PRINT "A has"; X; "elements"
100 PRINT "B has"; X+Y; "elements"
110 PRINT "C has"; X*2; "elements"
120 END 