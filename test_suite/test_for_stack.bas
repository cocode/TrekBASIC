10 REM Test that would previously cause FOR stack overflow
20 FOR I = 1 TO 100
30 FOR J = 1 TO 10
40 K = I * J
50 NEXT J
60 NEXT I
70 PRINT "Successfully completed 1000 total iterations!"
80 END 