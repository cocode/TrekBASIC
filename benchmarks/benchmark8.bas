10 REM From https://en.wikipedia.org/wiki/Rugg/Feldman_benchmarks
11 REM I think this is a poor benchmark, as it does not verify correctness.
12 REM It should accumulate results, and print the final answer.
300 PRINT"S"
400 K=0
500 K=K+1
530 A=K^2
540 B=LOG(K)
550 C=SIN(K)
600 IF K<1000 THEN GOTO 500
700 PRINT"E"
800 END
