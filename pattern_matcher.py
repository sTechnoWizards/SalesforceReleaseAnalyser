"""
Pattern Matcher
Fast local scanning of code for deprecated patterns
NO AI needed - just string matching (instant results!)
"""

import re
from typing import List, Dict


class PatternMatcher:
    """Fast pattern matching engine"""
    
    def __init__(self, breaking_changes):
        """
        Initialize with breaking changes from AI
        
        Args:
            breaking_changes: List of dicts with searchKeyword field
        """
        try:
            self.changes = breaking_changes
            self.keywords = [change['searchKeyword'] for change in breaking_changes]
            print(f"🔍 Pattern matcher initialized with {len(self.keywords)} patterns")
            
            if len(self.keywords) > 0:
                print(f"   Patterns: {', '.join(self.keywords[:5])}{'...' if len(self.keywords) > 5 else ''}")
            else:
                print("   ⚠️  WARNING: No patterns to search for!")
                
        except Exception as e:
            print(f"\n❌ ERROR initializing Pattern Matcher")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print(f"Breaking changes received: {breaking_changes}")
            raise
    
    def scan_apex_class(self, apex_class):
        """
        Scan a single Apex class for deprecated patterns
        
        Args:
            apex_class: Dict with name, code, apiVersion
            
        Returns:
            Dict with impact info or None
        """
        try:
            code = apex_class.get('code', '')
            if not code:
                return None
            
            found_patterns = []
            line_numbers = {}
            
            for keyword in self.keywords:
                if keyword in code:
                    # Find all occurrences and line numbers
                    lines = code.split('\n')
                    line_nums = [
                        i + 1 for i, line in enumerate(lines)
                        if keyword in line
                    ]
                    
                    if line_nums:
                        found_patterns.append(keyword)
                        line_numbers[keyword] = line_nums
            
            if found_patterns:
                # Find severity from breaking changes
                max_severity = 'LOW'
                recommendations = []
                
                for pattern in found_patterns:
                    for change in self.changes:
                        if change['searchKeyword'] == pattern:
                            if change['severity'] == 'HIGH':
                                max_severity = 'HIGH'
                            elif change['severity'] == 'MEDIUM' and max_severity != 'HIGH':
                                max_severity = 'MEDIUM'
                            
                            recommendations.append(
                                f"{pattern} → {change['alternative']}"
                            )
                
                return {
                    'name': apex_class['name'],
                    'type': 'ApexClass',
                    'foundPatterns': found_patterns,
                    'lineNumbers': line_numbers,
                    'severity': max_severity,
                    'recommendations': recommendations,
                    'apiVersion': apex_class.get('apiVersion', 'Unknown')
                }
            
            return None
            
        except Exception as e:
            print(f"   ⚠️  Error scanning {apex_class.get('name', 'Unknown')}: {str(e)}")
            return None
    
    def scan_lwc(self, lwc_component):
        """
        Scan LWC component (JS + HTML)
        
        Args:
            lwc_component: Dict with name, js, html
            
        Returns:
            Dict with impact info or None
        """
        js_code = lwc_component.get('js', '')
        html_code = lwc_component.get('html', '')
        full_code = js_code + '\n' + html_code
        
        if not full_code.strip():
            return None
        
        found_patterns = []
        line_numbers = {}
        
        for keyword in self.keywords:
            if keyword in full_code:
                # Track where found (JS vs HTML)
                locations = []
                if keyword in js_code:
                    locations.append('JavaScript')
                if keyword in html_code:
                    locations.append('HTML')
                
                found_patterns.append(keyword)
                line_numbers[keyword] = locations
        
        if found_patterns:
            max_severity = 'LOW'
            recommendations = []
            
            for pattern in found_patterns:
                for change in self.changes:
                    if change['searchKeyword'] == pattern:
                        if change['severity'] == 'HIGH':
                            max_severity = 'HIGH'
                        elif change['severity'] == 'MEDIUM' and max_severity != 'HIGH':
                            max_severity = 'MEDIUM'
                        
                        recommendations.append(
                            f"{pattern} → {change['alternative']}"
                        )
            
            return {
                'name': lwc_component['name'],
                'type': 'LWC',
                'foundPatterns': found_patterns,
                'locations': line_numbers,
                'severity': max_severity,
                'recommendations': recommendations
            }
        
        return None
    
    def scan_trigger(self, trigger):
        """Scan Apex trigger"""
        code = trigger.get('code', '')
        if not code:
            return None
        
        found_patterns = [kw for kw in self.keywords if kw in code]
        
        if found_patterns:
            return {
                'name': trigger['name'],
                'type': 'ApexTrigger',
                'object': trigger.get('object', 'Unknown'),
                'foundPatterns': found_patterns,
                'severity': 'HIGH'  # Triggers are critical
            }
        
        return None
    
    def scan_all_metadata(self, metadata):
        """
        Scan ALL org metadata for impacts
        This runs FAST - pure string matching, no AI!
        
        Args:
            metadata: Dict from SalesforceOrgScanner.get_all_metadata()
            
        Returns:
            List of impacted components
        """
        print("\n" + "="*60)
        print("🔎 Scanning Org for Deprecated Patterns")
        print("="*60 + "\n")
        
        impacts = []
        
        # Scan Apex Classes
        print(f"Scanning {len(metadata['apexClasses'])} Apex classes...")
        for cls in metadata['apexClasses']:
            result = self.scan_apex_class(cls)
            if result:
                impacts.append(result)
        print(f"   ✅ Found {len([i for i in impacts if i['type'] == 'ApexClass'])} impacted classes")
        
        # Scan Triggers
        print(f"Scanning {len(metadata['apexTriggers'])} triggers...")
        for trg in metadata['apexTriggers']:
            result = self.scan_trigger(trg)
            if result:
                impacts.append(result)
        print(f"   ✅ Found {len([i for i in impacts if i['type'] == 'ApexTrigger'])} impacted triggers")
        
        # Scan LWC
        print(f"Scanning {len(metadata['lwcComponents'])} LWC components...")
        for lwc in metadata['lwcComponents']:
            result = self.scan_lwc(lwc)
            if result:
                impacts.append(result)
        print(f"   ✅ Found {len([i for i in impacts if i['type'] == 'LWC'])} impacted LWCs")
        
        print("\n" + "="*60)
        print(f"🎯 Total Impacted Components: {len(impacts)}")
        print("="*60 + "\n")
        
        return impacts


# Test
if __name__ == "__main__":
    # Sample breaking changes
    breaking_changes = [
        {
            "searchKeyword": "@track",
            "severity": "HIGH",
            "alternative": "Use reactive properties"
        },
        {
            "searchKeyword": "UserInfo.getSessionId()",
            "severity": "HIGH",
            "alternative": "Use Named Credentials"
        }
    ]
    
    matcher = PatternMatcher(breaking_changes)
    
    # Sample Apex class
    sample_class = {
        'name': 'TestClass',
        'code': '''
public class TestClass {
    public void test() {
        String sessionId = UserInfo.getSessionId();
        System.debug(sessionId);
    }
}
        ''',
        'apiVersion': 60.0
    }
    
    result = matcher.scan_apex_class(sample_class)
    print(result)
