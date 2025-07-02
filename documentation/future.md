# Future

## Targets (WASM)
By using python and LLVM, we can run TrekBasic almost anywhere. 

We'd like to run in the browser, as some point. While I see no particular need for using basic to script web applications, but 
the idea amuses me. 

## Build a fuzzer

https://www.cse.unr.edu/~fredh/class/460/S2013/class/Papers/tanna.pdf

## Build a basic test runner, like junit.

We do some of this now, with REM EXPECT_EXIT_CODE=1
We could add asserts, but for now, we just use IF inside the test.
BASIC (older basic) lacks the idea of separate sections in the code, so I don't see 
a way to do multiple tests in a file cleanly.
And tests written in basic, to test the basic language,  are integration tests, not unit tests.
names: 'Binteration', "best", "BITR", "BIT", "RIT", "BRIT", "BASIT": BITR

See test_runner_common.py

### Possible Future Features:

* Specify expected return status for program
* Specify expected output
* Specify a timeout, to catch infinition loops.
* Detect if interpreter crashes, as opposed to clean exit
* Skip this test.
* Specify dialects that this test is relevant for.
* Parameterized testing: run N versions of the test, with different parameters.
* The interpreter provides code coverage. We could include that in the test_suite report.
    "This test suite covered xx% of the code."
* "auto-test" - find functions and write tests, based on their definitons. - that is more of a unit test thing.

 ### AI Player
we have TrekBot, which plays startrek badly. adding a chatbot player would be fun.
