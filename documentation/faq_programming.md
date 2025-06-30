# Programming Frequently Asked Questions

## Why can't this run other versions of Star Trek? Or Other Programs?
There are *so* many old versions of the BASIC programming language that the chance any old program will 
"Just run" on any given interpreter is about zero. 

You need to match the interpreter to the one the program was designed to run on. Unfortunately, the information
as to which interpreter is required is usually lost to history. 

If your program does not run, it's not that hard to add another support for another dialect. 
The challenge is figuring out what features and behaviors that this program requires. 
       
Sometimes, adding a new feature is simple and doesn't conflict with other implementations. For example, supporting both
<> and # to mean 'not equal' is not a problem.

But some versions of BASIC use zero-based arrays, some use one-based. Obviously, you can't support
both options at once. In this case, we have a setting in basic_dialect.py for this.

Some features are too much for a simple switch. Right now, we don't handle those features. An example would be not 
using line numbers. This should not be hard to implement, but it's a fundamental change that affects more than
just parsing (The renumber command should be removed). Another example would be supporting multicharacter variable 
names. This would fundamentally change the parser


A new dialect of basic would consist of

* Operators
* Keywords
* Statements
* ParsedStatements
* Tests for the above

The above are changes that don't alter the structure
of the language too much. 

Supporting a BASIC dialect with fundamental structural
differences like the following would be harder.

* Not having line numbers
* Multicharacter variable names


### Pluggable
One way to support a wider range of features is to have multiple parsers, 
and you would select the one needed to run your program.
 
### Generation of Parsers
One technique used to support multiple architectures is to generate the code from a common definition file. This 
is commonly done to generate toolkits for APIs in multiple langauges. This has the advantages of generating a clean 
version of the parser, etc., without a bunch of ifs. 

Code generation should be quick, it's possible we could do generation at run-time.

### Auto-detection
Auto-detection of basic variants sounds possible, but might be hard to get right. Figuring out a dialect uses
"#" for not equals, and "!" for remarks is easy. Figuring out associativity for exponentiation,  or whether 
"arrays start at 1 or 0" is harder.

### Current Dialect
Currently, TrekBasic only supports one dialect, the one that runs 
programs/superstartrek.bas. It has a few added non-conflicting features, like allowing
"#" for not equals, in addition to "<>", so it can run hunt_the_wumpus.
 
### More Reading
This document describes the compatibility issues between various versions of BASIC: 
 https://files.eric.ed.gov/fulltext/ED083819.pdf


## Is there more information available?
We built this off information I found on the web, so, yes.
See the file references.md, there's a lot.