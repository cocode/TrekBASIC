0 REM Eratosthenes Sieve Prime Number Program in BASIC
1 S1 = 8190
2 DIM F(8191)
3 PRINT "Only 1 iteration"
5 C = 0
6 FOR I = 0 TO S1
7 F(I) = 1
8 NEXT I
9 FOR I = 0 TO S1
10 IF F(I) = 0 THEN 18
11 P = I+I + 3
12 K = I + P
13 IF K > S1 THEN 17
14 F (K) = 0
15 K = K + P
16 GOTO 13
17 C = C + 1
18 NEXT I
19 PRINT C;" PRIMES"