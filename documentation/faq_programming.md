# Programming Frequently Asked Questions

## Basic Incompatibilities

There are *so* many old versions of the BASIC programming language that the chance any old program will 
"Just run" on any given interpreter is about zero. 

You need to match the interpreter to the one the program was designed to run on. Unfortunately, the information
as to which interpreter (or what features are needed) is required is usually lost to history. 

If your program does not run, it's not that hard to add another support for another dialect. 
The challenge is figuring out what features and behaviors that this program requires. 
       
Sometimes, adding a new feature is simple and doesn't conflict with other implementations. For example, supporting both
<> and # to mean 'not equal' is not a problem.

But some versions of BASIC use zero-based arrays, some use one-based. Obviously, you can't support
both options at once. In this case, we have a setting in ***basic_dialect.py*** for this. We also support two 
different lexers - one for the older, compressed style **FORA=BTOCSTEPD** one for the newer **FOR A = B TO C STEP D**.
Look at ***basic_lexer.py***

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
One way to support a wider range of features is to have multiple lexers or parsers, 
and you would select the one needed to run your program. We currently have two pluggable lexers, which
you can change in the shell at run time. Switching lexers at runtime is really only for testing new lexers.
 
### Generation of Parsers
One technique used to support multiple architectures is to generate the code from a common definition file. This 
is commonly done to generate toolkits for APIs in multiple languages. This has the advantages of generating a clean 
version of the parser, etc., without a bunch of ifs. 

Code generation should be quick, it's possible we could do generation at run-time.

### Auto-detection
Auto-detection of basic variants sounds possible, but might be hard to get right. Figuring out a dialect uses
"#" for not equals, and "!" for remarks is easy. Figuring out associativity for exponentiation, or whether 
"arrays start at 1 or 0" is harder.

### Current Dialect
Currently, TrekBasic only supports one dialect, the one that runs 
programs/superstartrek.bas. It has a few added non-conflicting features, like allowing
"#" for not equals, in addition to "<>", so it can run hunt_the_wumpus.

It does have multiple settings in basic_dialect.py, so it can support more than just one version.
 
### More Reading
This document describes the compatibility issues between various versions of BASIC: 
 https://files.eric.ed.gov/fulltext/ED083819.pdf


## Terminology
A LINE is made up of multiple STATEMENTS, each one beginning with a KEYWORD.

### LINE
    100 PRINT X:GOTO 200
### STATEMENTS
    "PRINT X" and "GOTO 100"
### KEYWORDS
    "PRINT", and "GOTO"


## Is there more information available?
We built this off information I found on the web, so, yes.
See the file references.md, there's a lot.


# Tests

We have unit tests, written in python, and integration tests, written in BASIC. Since the tests in BASIC 
can be shared across all 6 implementations of BASIC in the TrekBasic family, the tests written in BASIC
have been moved to their own project. You'll need to check out that project to run the integration tests.

6 = 3 implementations (Python, Java, Rust) x (interpreter, compiler)

See BasicTestSuite in README.md

## All Tests
In the project directory

```./run_all_tests.py```

## Basic (Integration)
In the project directory

To run unit and integration (.bas) tests:

```./run_all_tests.py -i```

That runs them with the interpreter.

```./run_all_tests.py -l```

Runs them with the compiler. l is for LLVM.

### Run One Basic Test

```
python -m trekbasicpy.basic test_loading.bas
```
or with the compiler
```
python -m trekbasicpy.tbc  ~/source/basic_test_suite/test_loading.bas
```

## Unit tests
Against the interpreter:

```./run_all_tests.py -u```

No unit test are currently availabe for the compiler. Note the compiler
uses the same lexing/parsing etc. Only the codegen is different. 
This is a lack, but not as bad as it might sound.


## Code Coverage

run
```
./run_coverage_tests.py ~/source/basic_test_suite
```