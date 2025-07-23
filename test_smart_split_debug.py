#!/usr/bin/env python3

from trekbasicpy.basic_utils import smart_split

def test_smart_split_cases():
    """Test various smart_split cases for IF THEN ELSE"""
    
    print("Testing smart_split with various IF THEN ELSE scenarios...")
    print("=" * 60)
    
    # Test case 1: IF THEN ELSE with statements after (from failing test)
    test1 = 'IF A>0 THEN B=1 ELSE B=0: PRINT B: GOTO 100'
    result1 = smart_split(test1)
    print(f"Test 1: {test1}")
    print(f"Result: {result1}")
    print(f"Expected: ['IF A>0 THEN B=1 ELSE B=0', ' PRINT B', ' GOTO 100'] (3 parts)")
    print(f"Actual length: {len(result1)}")
    print()
    
    # Test case 2: IF THEN ELSE with multiple statements in both clauses (from our bug)
    test2 = 'IF A > 0 THEN E = 10 : F = 20 ELSE E = 30 : F = 40'
    result2 = smart_split(test2)
    print(f"Test 2: {test2}")
    print(f"Result: {result2}")
    print(f"Expected: ['IF A > 0 THEN E = 10 : F = 20 ELSE E = 30 : F = 40'] (1 part)")
    print(f"Actual length: {len(result2)}")
    print()
    
    # Test case 3: Simple IF THEN ELSE without extra statements
    test3 = 'IF A>0 THEN PRINT "Positive" ELSE PRINT "Not positive"'
    result3 = smart_split(test3)
    print(f"Test 3: {test3}")
    print(f"Result: {result3}")
    print(f"Expected: ['IF A>0 THEN PRINT \"Positive\" ELSE PRINT \"Not positive\"'] (1 part)")
    print(f"Actual length: {len(result3)}")
    print()
    
    # Test case 4: IF THEN without ELSE
    test4 = 'IF A>0 THEN PRINT "Positive": B=1'
    result4 = smart_split(test4)
    print(f"Test 4: {test4}")
    print(f"Result: {result4}")
    print(f"Expected: ['IF A>0 THEN PRINT \"Positive\": B=1'] (1 part)")
    print(f"Actual length: {len(result4)}")
    print()
    
    # Test case 5: Regular statements (no IF)
    test5 = 'PRINT "Hello": X = 5: GOTO 100'
    result5 = smart_split(test5)
    print(f"Test 5: {test5}")
    print(f"Result: {result5}")
    print(f"Expected: ['PRINT \"Hello\"', ' X = 5', ' GOTO 100'] (3 parts)")
    print(f"Actual length: {len(result5)}")
    print()

if __name__ == "__main__":
    test_smart_split_cases() 