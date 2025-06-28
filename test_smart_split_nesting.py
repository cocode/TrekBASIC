#!/usr/bin/env python3

from basic_utils import smart_split

def test_smart_split_nesting():
    """Test smart_split with nested parentheses"""
    
    print("Testing smart_split with nested parentheses...")
    print("=" * 60)
    
    # Test case from user: DIM X( MAX(MAX(Z,A), A ))
    test1 = "X( MAX(MAX(Z,A), A )), Y(3), Z(A+B)"
    result1 = smart_split(test1, enquote="(", dequote=")", split_char=",")
    print(f"Test 1: {test1}")
    print(f"Result: {result1}")
    print(f"Expected: ['X( MAX(MAX(Z,A), A ))', ' Y(3)', ' Z(A+B)'] (3 parts)")
    print(f"Actual length: {len(result1)}")
    print()
    
    # Test case with simple parentheses (should still work)
    test2 = "A(3,4), B(5,6), C(7)"
    result2 = smart_split(test2, enquote="(", dequote=")", split_char=",")
    print(f"Test 2: {test2}")
    print(f"Result: {result2}")
    print(f"Expected: ['A(3,4)', ' B(5,6)', ' C(7)'] (3 parts)")
    print(f"Actual length: {len(result2)}")
    print()
    
    # Test case with string quotes (should work as before)
    test3 = 'PRINT"Hello, World": PRINT"Goodbye"'
    result3 = smart_split(test3, enquote='"', dequote='"', split_char=":")
    print(f"Test 3: {test3}")
    print(f"Result: {result3}")
    print(f"Expected: ['PRINT\"Hello, World\"', ' PRINT\"Goodbye\"'] (2 parts)")
    print(f"Actual length: {len(result3)}")
    print()
    
    # Test case with deeply nested parentheses
    test4 = "A(B(C(D,E),F),G), H(I)"
    result4 = smart_split(test4, enquote="(", dequote=")", split_char=",")
    print(f"Test 4: {test4}")
    print(f"Result: {result4}")
    print(f"Expected: ['A(B(C(D,E),F),G)', ' H(I)'] (2 parts)")
    print(f"Actual length: {len(result4)}")
    print()

if __name__ == "__main__":
    test_smart_split_nesting() 