10 DIM S(3,3), N(5), T$(2,2)
20 DATA 1.5, 2.7, 3.14, "HELLO", "WORLD", "TEST"
30 READ S(1,1), S(2,2), S(3,3)
40 READ T$(1,1), T$(2,2), T$(1,2)
50 PRINT "S(1,1)="; S(1,1); " S(2,2)="; S(2,2); " S(3,3)="; S(3,3)
60 PRINT "T$(1,1)="; T$(1,1); " T$(2,2)="; T$(2,2); " T$(1,2)="; T$(1,2)
70 PRINT "READ into array elements works!"
80 END 