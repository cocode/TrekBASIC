100 REM Test some string operations
110 A$ = "This is a test"
120 L$ = LEFT$(A$, 4)
130 PRINT L$
140 R$ = RIGHT$(A$, 4)
150 M$ = MID$(A$, 6, 2)
160 D$ = L$ + M$ + R$
170 IF D$ <> "Thisistest" THEN STOP
180 END

