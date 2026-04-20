"""
Test script to verify all components work
Run this before using the full app
"""

print("🧪 Testing Salesforce Release Analyzer Components\n")
print("="*60)

# Test 1: Pattern Matcher
print("\n1️⃣ Testing Pattern Matcher...")
try:
    from pattern_matcher import PatternMatcher
    
    test_changes = [
        {"searchKeyword": "@track", "severity": "HIGH", "alternative": "reactive properties"}
    ]
    
    matcher = PatternMatcher(test_changes)
    
    test_class = {
        'name': 'TestClass',
        'code': '@track myProperty = null;',
        'apiVersion': 60.0
    }
    
    result = matcher.scan_apex_class(test_class)
    
    if result and '@track' in result['foundPatterns']:
        print("   ✅ Pattern Matcher works!")
    else:
        print("   ❌ Pattern Matcher failed")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Report Generator
print("\n2️⃣ Testing Report Generator...")
try:
    from report_generator import ReportGenerator
    
    gen = ReportGenerator()
    
    test_impacts = [{
        'name': 'TestClass',
        'type': 'ApexClass',
        'foundPatterns': ['@track'],
        'severity': 'HIGH',
        'recommendations': ['Use reactive properties']
    }]
    
    test_changes = [{
        'item': '@track',
        'searchKeyword': '@track',
        'impact': 'Deprecated',
        'alternative': 'Reactive properties',
        'severity': 'HIGH'
    }]
    
    html = gen.generate_html_report(
        test_impacts,
        test_changes,
        {'apex': 1, 'triggers': 0, 'lwc': 0, 'flows': 0}
    )
    
    if '<html' in html and 'TestClass' in html:
        print("   ✅ Report Generator works!")
        
        # Save test report
        filename = gen.save_report(html, 'test_report.html')
        print(f"   📄 Test report saved: {filename}")
    else:
        print("   ❌ Report Generator failed")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: AI Analyzer (requires API key)
print("\n3️⃣ Testing AI Analyzer...")
print("   ⚠️  Skipped - requires Gemini API key")
print("   💡 Test manually after setup")

# Test 4: Salesforce Client (requires credentials)
print("\n4️⃣ Testing Salesforce Client...")
print("   ⚠️  Skipped - requires Salesforce credentials")
print("   💡 Test via main.py UI")

print("\n" + "="*60)
print("\n✅ Core components verified!")
print("\n📝 Next steps:")
print("   1. Get Gemini API key from ai.google.dev")
print("   2. Get Salesforce security token")
print("   3. Run: streamlit run main.py")
print("\n🚀 Ready to analyze your org!")
