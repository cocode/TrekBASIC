10 REM From https://en.wikipedia.org/wiki/Rugg/Feldman_benchmarks
300 PRINT"S"
400 K=0
500 K=K+1
510 LET A=K/2*3+4-5
520 GOSUB 820
600 IF K<1000 THEN 500
700 PRINT"E"
800 END
820 RETURN