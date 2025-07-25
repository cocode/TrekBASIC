
# Game Frequently Asked Questions

Full directions for the game can be found here:
https://coding-horror.github.io/basic-computer-games/84_Super_Star_Trek/javascript/index.html

## Short directions

Use the command **SRS** to see what is in your current area

Use the command **LRS** to see what is in adjacent squares

213 in **LRS** output means 2 klingons, 1 starbase, and 3 stars.

Use the command **COM**, then "0" to see a full quadrant map. It only shows information for
quadrants you have visited or scanned.

Move around the map, shooting Klingons with commands **PHA**sers or **TOR**pedoes. If you run low on energy or 
take damage, find a starbase to recharge.

If you don't raise **SHE**ilds first, you'll die at the first shot from a Klingon.

The game is turn limited, so don't waste too much time wandering around.


## Navigation
### Directions
```
┌─────┬─────┬─────┐
│  4  │  3  │  2  │
│  ↖  │  ↑  │  ↗  │
├─────┼─────┼─────┤
│  5  │  ●  │  1  │
│  ←  │ YOU │  →  │
├─────┼─────┼─────┤
│  6  │  7  │  8  │
│  ↙  │  ↓  │  ↘  │
└─────┴─────┴─────┘
```

### Directions and Warp Factors
Directions and warp factors can contain decimals.

## Computer Commands

Source: https://www.atariarchives.org/bcc1/showpage.php?page=276

You access these commands with the **COM** command at the main menu. 

Library computer options are as follows (more complete descriptions are in program instructions, above):

 0   Cumulative galactic record
 1   Status report
 2   Photon torpedo course data
 3   Starbase navigation data
 4   Direction/distance calculator
 5   Quadrant nomenclature map


