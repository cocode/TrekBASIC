# Documentation for superstartrek.bas

### VARIABLES
* G(8,8) is the Galaxy, and 8x8 array of quadrants, each made up of 8x8 sectors.
  * In each cell is a number from 0-1000:
    * Hundreds place is klingons, 0-3
    * Tens place starbases. 0-1
    * Ones place is stars
* K9 Number of klingons in the galaxy
* B9 Number of bases in the galaxy
* A$ can be the enterprise "<*>", a Klingon "+k+", >!<
  * Seems to be a holder of "the current object"
* K3 number of Klingons in a quadrant
* B3 Number of bases in a quadrant
* S3 Number of stars
* K(3) is the positions of the 1-3 Klingons in this sector
* S is the current shield level. Under 200 gives a warning.
* E is energy. Total energy is S+E, default energy level is E0
  I think S is shields.
* Q1, Q2 are the Quadrant co-ordinates (indices into G())
* S1, S2 are the sector co-ordinates (of the enterprise?)
* Q$ Is is possible that the current sector is stored in a string?
    "8660 REM INSERT IN STRING ARRAY FOR QUADRANT", so probably yes.
* Z(8,8) is the part of the galaxy you have already seen.

Q1=FNR(1):Q2=FNR(1):S1=FNR(1):S2=FNR(1)


## Line Numbers / Subroutines
All numbers are for supersstartrek.bas.
1500 is the main sector status report.

1600 goes here if the coordinates are out of the sector, chooses new position?

1720 place klingons, if any Array K is the positions of the 1-3 klingons in this secor

2060 Main command input
2140 branches for each command: 2140 ONIGOTO2300,1980,4000,4260,4700,5530,5690,7290,6270
4000 Long Range Sensor command
4030 Print long range sensor results. N(3) is the current line's three squares. 
    if n(x)<0, then that quadrant is out of the galaxy.
    Z(8,8) is the record of the galaxy that you have already seen. You can print it with
    comand "COM", followed by computer command 0
**1990** checks energy. It does not appear to be syntactically valid, but is
not rasing an error

4850 Follow photon torpedo track, and see what it hits.
6820 print status report


8590: Generate some random numbers
8660 REM INSERT IN STRING ARRAY FOR QUADRANT
8660 REM INSERT IN STRING ARRAY FOR QUADRANT
2060 Main? input



## Variab
Gmight be the current sector, with the different items in different decimal places
1500 PRINT:K3=INT(G(Q1,Q2)*.01):B3=INT(G(Q1,Q2)*.1)-10*K3
1540 S3=G(Q1,Q2)-100*K3-10*B3:IFK3=0THEN1590
REM "B3" STARBASES, & "S3" STARS ELSEWHERE.

1540 the if is "if there are no klingons"




