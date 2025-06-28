# Programming Frequently Asked Questions

## Why can't this run other versions of Star Trek?
    
   It's not that hard to add another version. The challenge is figuring out what features
   and behaviors that version of Star Trek requires. 
       
   For example, some versions of BAISC use
   zero-based arrays, some use one-based. Unfortunately, sometimes adding suppport for one version
   means breaking support for another.
   Where we can increase support by adding features that don't conflict, like new functions,
   we should. 

A new dialect of basic would consist of

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
* Differences in associativity (such as Exponentiation, below)

I've just downloaded the original "Hunt the Wumpus". It uses DATA and READ statements. I'll have to implement them.
this won't conflict with anything in the current implementation.

### Exponentiation.
Exponentiation is currently left associative, as opposed to the more standard right association. We do this because 
older dialects of basic had it that way, and we are currently emulating older versions.

## Is there more information available?
We built this off information I found on the web, so, yes.
See the file references.md, there's a lot.