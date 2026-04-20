"""
Test script to verify field pattern matching
"""

import re

def test_field_pattern(field_name):
    """Test if field pattern matches various code patterns"""
    
    # Updated pattern from field_analyzer.py
    field_pattern = re.compile(
        rf'(?:^|[\s\[\(,=!<>+\-*/:"\'{{$])(?:[\w\.]*\.)?{re.escape(field_name)}(?=[\s\]\),;=!<>+\-*/:"\'}}]|$)',
        re.IGNORECASE
    )
    
    # Test cases
    test_cases = [
        # Apex patterns
        ("record.Category__c", True),
        ("c.Category__c", True),
        ("obj.Category__c", True),
        ("myCase.Category__c", True),
        ("Category__c", True),
        ("if (Category__c != null)", True),
        ("String cat = Category__c;", True),
        ("record.get('Category__c')", True),
        ("SObjectField Category__c = ", True),
        
        # Should NOT match
        ("CategoryValue__c", False),  # Different field
        ("// Category__c is deprecated", True),  # In comment - should match but marked as comment
        
        # JavaScript patterns
        ("record.Category__c", True),
        ("this.Category__c", True),
        ("data.Category__c", True),
        ("{Category__c}", True),
        
        # Flow/SOQL patterns
        ("$Record.Category__c", True),
        ("WHERE Category__c =", True),
        ("SELECT Category__c FROM", True),
        ('"field": "Category__c"', True),
    ]
    
    print(f"\nTesting pattern for field: {field_name}")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for code_snippet, should_match in test_cases:
        match = field_pattern.search(code_snippet)
        matched = match is not None
        
        if matched == should_match:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"{status} | Expected: {should_match:5} | Got: {matched:5} | {code_snippet}")
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    # Test with actual field from user's case
    success = test_field_pattern("Category__c")
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed - pattern may need adjustment")
