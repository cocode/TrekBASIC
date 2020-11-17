# Documentation for superstartrek.bas

### VARIABLES
A$ can be the enterprise "<*>", a kingon "+k+", >!<
K3 number of klingons
B3 Number of bases
S3 Number of stars
Array G current sector? No, I think it is the 8x8 galaxy of 8x8 sectors.
Array K is the positions of the 1-3 klingons in this secor
S is the current shield level. Under 200 gives a warning.
E is energy. Total energy is S+E, default energy level is E0

Q1=FNR(1):Q2=FNR(1):S1=FNR(1):S2=FNR(1)

Q1, Q2 are the Quadrant, S1, S2 are the sector co-ordinates

## Line Numbers / Subroutines
**1990** checks energy. It does not appear to be syntactically valid, but is
not rasing an error

8590: Generate some random numbers

2060 Main? input

6820 print status report

1500 is the main sector status report.

1600 goes here if the coordinates are out of the sector, chooses new position?

1720 place klingons, if any Array K is the positions of the 1-3 klingons in this secor

## Tentative
G might be the current sector, with the different items in different decimal places
1500 PRINT:K3=INT(G(Q1,Q2)*.01):B3=INT(G(Q1,Q2)*.1)-10*K3
1540 S3=G(Q1,Q2)-100*K3-10*B3:IFK3=0THEN1590
REM "B3" STARBASES, & "S3" STARS ELSEWHERE.

1540 the if is "if there are no klingons"
Hundreds place might be Klingons
Tens place B3, bases?
Ones place is stars S3

A$ can be the enterprise "<*>", a kingon "+k+", >!<
So K3 (hundreds place) might be nunber of klingons in the sector.
[[1.0, 4.0, 4.0, 8.0, 101.0, 4.0, 1.0, 4.0],
 [2.0, 1.0, 106.0, 17.0, 6.0, 4.0, 103.0, 7.0],
 [1.0, 4.0, 6.0, 4.0, 5.0, 1.0, 8.0, 2.0],
 [17.0, 2.0, 5.0, 5.0, 207.0, 106.0, 105.0, 7.0],
 [5.0, 3.0, 5.0, 2.0, 7.0, 7.0, 6.0, 1.0],
 [1.0, 1.0, 2.0, 4.0, 1.0, 2.0, 5.0, 7.0],
 [2.0, 6.0, 2.0, 205.0, 4.0, 6.0, 8.0, 107.0],
 [6.0, 1.0, 107.0, 202.0, 116.0, 3.0, 4.0, 6.0]]
<SymbolType.ARRAY: 3>


Array G, maybe current sector?

