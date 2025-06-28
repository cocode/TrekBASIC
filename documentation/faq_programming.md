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

Supporting a BASIC dialect with fundamental structural
differences would be much harder.
Differences like not having line numbners, or 
differences in associativity (Exponenetiation, below)
would be much more work.
   
### Exponentiation.
Why is exponentiation right associative? It's currently left associative, as older dialects of basic had it that way, and currently
we are emulating older version, that inlclude lines numbers amoung
other things

## Is there more information available?
We built this off information I found on the web, so, yes.
See the file references.md, there's a lot.