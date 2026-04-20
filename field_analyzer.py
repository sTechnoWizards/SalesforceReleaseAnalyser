"""
Field Usage Analyzer
Comprehensive analysis of where Salesforce fields are used across all components
"""

import re
from typing import List, Dict, Any
import pandas as pd


class FieldUsageAnalyzer:
    """Analyze field usage across all Salesforce components"""
    
    def __init__(self, salesforce_client):
        """
        Initialize analyzer with Salesforce client
        
        Args:
            salesforce_client: SalesforceOrgScanner instance
        """
        self.sf_client = salesforce_client
        self.results = []
    
    def analyze_field_usage(self, object_fields_map: Dict[str, List[str]], metadata: Dict[str, Any]) -> List[Dict]:
        """
        Analyze usage of specified fields across all components
        
        Args:
            object_fields_map: Dict with object names as keys and list of field API names as values
                              Example: {'Account': ['Name', 'Industry'], 'Contact': ['Email']}
            metadata: Dict containing all org components (apex, triggers, lwc, flows)
        
        Returns:
            List of usage analysis results
        """
        print("\n" + "="*60)
        print("🔍 FIELD USAGE ANALYSIS STARTING")
        print("="*60)
        
        # Debug: Show metadata counts
        print(f"\n📦 Components available for analysis:")
        print(f"   - Apex Classes: {len(metadata.get('apex', []))}")
        print(f"   - Triggers: {len(metadata.get('triggers', []))}")
        print(f"   - LWC Components: {len(metadata.get('lwc', []))}")
        print(f"   - Flows: {len(metadata.get('flows', []))}")
        
        self.results = []
        
        # Get data statistics for all fields
        field_stats = self._get_field_statistics(object_fields_map)
        
        # Analyze each component type
        for obj_name, field_names in object_fields_map.items():
            for field_name in field_names:
                field_key = f"{obj_name}.{field_name}"
                print(f"\n📊 Analyzing field: {field_key}")
                
                # Get data stats for this field
                stats = field_stats.get(field_key, {})
                
                # Search in Apex classes
                self._search_in_apex(obj_name, field_name, metadata.get('apex', []), stats)
                
                # Search in Triggers
                self._search_in_triggers(obj_name, field_name, metadata.get('triggers', []), stats)
                
                # Search in LWC components
                self._search_in_lwc(obj_name, field_name, metadata.get('lwc', []), stats)
                
                # Search in Flows
                self._search_in_flows(obj_name, field_name, metadata.get('flows', []), stats)
        
        print(f"\n✅ Analysis complete: Found {len(self.results)} usages")
        return self.results
    
    def _get_field_statistics(self, object_fields_map: Dict[str, List[str]]) -> Dict[str, Dict]:
        """
        Get data statistics for all specified fields
        
        Returns:
            Dict with field_key as key and stats as value
        """
        print("\n📈 Fetching field data statistics...")
        field_stats = {}
        
        for obj_name, field_names in object_fields_map.items():
            try:
                stats = self.sf_client.get_field_data_stats(obj_name, field_names)
                for field_name, stat in stats.items():
                    field_key = f"{obj_name}.{field_name}"
                    field_stats[field_key] = stat
                    
                    # Print appropriate message based on filterability
                    if not stat.get('filterable', True):
                        note = stat.get('note', 'Non-filterable')
                        print(f"   ⚠️  {field_key}: {note} - stats unavailable, but usage analysis will proceed")
                    elif 'error' in stat:
                        print(f"   ⚠️  {field_key}: Error - {stat.get('error', 'Unknown error')[:100]}")
                    else:
                        print(f"   ✓ {field_key}: {stat.get('populated_count', 0):,} / {stat.get('total_count', 0):,} records ({stat.get('population_pct', 0):.1f}%)")
            except Exception as e:
                print(f"   ⚠️  Error fetching stats for {obj_name}: {str(e)}")
        
        return field_stats
    
    def _search_in_apex(self, obj_name: str, field_name: str, apex_classes: List[Dict], stats: Dict):
        """Search for field usage in Apex classes"""
        # Match field with optional dot prefix (e.g., record.FieldName__c) or in quotes
        # Also handles: record.get('FieldName__c'), SObjectType.FieldName__c, etc.
        field_pattern = re.compile(
            rf'(?:^|[\s\[\(,=!<>+\-*/:"\'\'{{])(?:[\w\.]*\.)?{re.escape(field_name)}(?=[\s\]\),;=!<>+\-*/:"\'\'}}]|$)',
            re.IGNORECASE
        )
        
        print(f"   🔍 Searching in {len(apex_classes)} Apex classes...")
        found_count = 0
        classes_with_code = 0
        
        for apex_class in apex_classes:
            code = apex_class.get('code', '')
            class_name = apex_class.get('name', 'Unknown')
            
            if code:
                classes_with_code += 1
            
            if not code:
                continue
            
            # Search for field usage
            for line_num, line in enumerate(code.split('\n'), 1):
                if field_pattern.search(line):
                    # Check if in comment
                    is_commented = self._is_commented_apex(line)
                    
                    # Check if this is a variable declaration (false positive)
                    is_variable_declaration = self._is_variable_declaration(line, field_name)
                    
                    # Skip if it's likely a variable declaration, not field usage
                    if is_variable_declaration and not is_commented:
                        continue
                    
                    # Try to find containing method
                    method = self._find_apex_method(code, line_num)
                    
                    found_count += 1
                    self.results.append({
                        'object': obj_name,
                        'field': field_name,
                        'component_type': 'Apex Class',
                        'component_name': class_name,
                        'file_type': 'APEX',
                        'line_number': line_num,
                        'method_name': method,
                        'code_snippet': line.strip(),
                        'is_commented': is_commented,
                        'is_active': not is_commented,
                        'total_records': stats.get('total_count', 0),
                        'populated_records': stats.get('populated_count', 0),
                        'population_percentage': stats.get('population_pct', 0.0)
                    })
        
        if found_count > 0:
            print(f"      ✅ Found {found_count} usage(s) in Apex")
        else:
            print(f"      ⚪ No usages found in Apex")
        
        if classes_with_code < len(apex_classes):
            print(f"      ⚠️  {classes_with_code}/{len(apex_classes)} classes had code")
    
    def _search_in_triggers(self, obj_name: str, field_name: str, triggers: List[Dict], stats: Dict):
        """Search for field usage in Triggers"""
        # Match field with optional dot prefix or in quotes
        field_pattern = re.compile(
            rf'(?:^|[\s\[\(,=!<>+\-*/:"\'\'{{])(?:[\w\.]*\.)?{re.escape(field_name)}(?=[\s\]\),;=!<>+\-*/:"\'\'}}]|$)',
            re.IGNORECASE
        )
        
        print(f"   🔍 Searching in {len(triggers)} Triggers...")
        found_count = 0
        triggers_with_code = 0
        
        for trigger in triggers:
            code = trigger.get('code', '')
            trigger_name = trigger.get('name', 'Unknown')
            trigger_obj = trigger.get('object', '')
            
            if code:
                triggers_with_code += 1
            
            if not code:
                continue
            
            # Search for field usage
            for line_num, line in enumerate(code.split('\n'), 1):
                if field_pattern.search(line):
                    is_commented = self._is_commented_apex(line)
                    
                    # Check if this is a variable declaration
                    is_variable_declaration = self._is_variable_declaration(line, field_name)
                    if is_variable_declaration and not is_commented:
                        continue
                    
                    found_count += 1
                    self.results.append({
                        'object': obj_name,
                        'field': field_name,
                        'component_type': 'Trigger',
                        'component_name': f"{trigger_name} (on {trigger_obj})",
                        'file_type': 'APEX',
                        'line_number': line_num,
                        'method_name': 'Trigger Context',
                        'code_snippet': line.strip(),
                        'is_commented': is_commented,
                        'is_active': not is_commented,
                        'total_records': stats.get('total_count', 0),
                        'populated_records': stats.get('populated_count', 0),
                        'population_percentage': stats.get('population_pct', 0.0)
                    })
        
        if found_count > 0:
            print(f"      ✅ Found {found_count} usage(s) in Triggers")
        else:
            print(f"      ⚪ No usages found in Triggers")
        
        if triggers_with_code < len(triggers):
            print(f"      ⚠️  {triggers_with_code}/{len(triggers)} triggers had code")
    
    def _search_in_lwc(self, obj_name: str, field_name: str, lwc_components: List[Dict], stats: Dict):
        """Search for field usage in LWC components"""
        # Match field in JS/HTML - handles quotes, curly braces, dot notation
        field_pattern = re.compile(
            rf'(?:^|[\s\[\(,=!<>+\-*/:"\'\'{{$])(?:[\w\.]*\.)?{re.escape(field_name)}(?=[\s\]\),;=!<>+\-*/:"\'\'}}]|$)',
            re.IGNORECASE
        )
        
        print(f"   🔍 Searching in {len(lwc_components)} LWC components...")
        found_count = 0
        components_with_source = 0
        
        for lwc in lwc_components:
            component_name = lwc.get('name', 'Unknown')
            source_files = lwc.get('source_files', {})
            
            if source_files:
                components_with_source += 1
            
            # Search in each file (JS, HTML, CSS, etc.)
            for filename, source_code in source_files.items():
                if not source_code:
                    continue
                
                file_ext = filename.split('.')[-1].upper() if '.' in filename else 'UNKNOWN'
                
                for line_num, line in enumerate(source_code.split('\n'), 1):
                    if field_pattern.search(line):
                        is_commented = self._is_commented_lwc(line, file_ext)
                        
                        # Check if this is a variable declaration
                        is_variable_declaration = self._is_variable_declaration(line, field_name)
                        if is_variable_declaration and not is_commented:
                            continue
                        
                        # Try to find containing function (for JS files)
                        method = 'N/A'
                        if file_ext == 'JS':
                            method = self._find_js_function(source_code, line_num)
                        
                        found_count += 1
                        self.results.append({
                            'object': obj_name,
                            'field': field_name,
                            'component_type': 'LWC',
                            'component_name': f"{component_name}/{filename}",
                            'file_type': file_ext,
                            'line_number': line_num,
                            'method_name': method,
                            'code_snippet': line.strip(),
                            'is_commented': is_commented,
                            'is_active': not is_commented,
                            'total_records': stats.get('total_count', 0),
                            'populated_records': stats.get('populated_count', 0),
                            'population_percentage': stats.get('population_pct', 0.0)
                        })
        
        if found_count > 0:
            print(f"      ✅ Found {found_count} usage(s) in LWC")
        else:
            print(f"      ⚪ No usages found in LWC")
        
        if components_with_source < len(lwc_components):
            print(f"      ⚠️  {components_with_source}/{len(lwc_components)} components had source code")
    
    def _search_in_flows(self, obj_name: str, field_name: str, flows: List[Dict], stats: Dict):
        """Search for field usage in Flows"""
        # Match field in JSON/XML - handles $Record.Field, quotes, etc.
        field_pattern = re.compile(
            rf'(?:^|[\s\[\(,=!<>:"\'\'{{$])(?:[\w\.]*\.)?{re.escape(field_name)}(?=[\s\]\),;=!<>:"\'\'}}]|$)',
            re.IGNORECASE
        )
        
        print(f"   🔍 Searching in {len(flows)} Flows...")
        found_count = 0
        flows_with_xml = 0
        
        for flow in flows:
            flow_name = flow.get('name', 'Unknown')
            flow_xml = flow.get('flow_xml', '')
            
            if flow_xml:
                flows_with_xml += 1
            
            if not flow_xml:
                continue
            
            # Search in flow metadata
            for line_num, line in enumerate(flow_xml.split('\n'), 1):
                if field_pattern.search(line):
                    # Extract context from JSON structure
                    context = self._extract_flow_context(flow_xml, line_num, field_name)
                    
                    found_count += 1
                    self.results.append({
                        'object': obj_name,
                        'field': field_name,
                        'component_type': 'Flow',
                        'component_name': flow_name,
                        'file_type': 'FLOW',
                        'line_number': line_num,
                        'method_name': context,
                        'code_snippet': line.strip()[:200],  # Limit length
                        'is_commented': False,  # Flows don't have comments in metadata
                        'is_active': True,
                        'total_records': stats.get('total_count', 0),
                        'populated_records': stats.get('populated_count', 0),
                        'population_percentage': stats.get('population_pct', 0.0)
                    })
        
        if found_count > 0:
            print(f"      ✅ Found {found_count} usage(s) in Flows")
        else:
            print(f"      ⚪ No usages found in Flows")
        
        if flows_with_xml < len(flows):
            print(f"      ⚠️  {flows_with_xml}/{len(flows)} flows had metadata")
    
    def _is_commented_apex(self, line: str) -> bool:
        """Check if line is commented in Apex code"""
        stripped = line.strip()
        return (
            stripped.startswith('//') or 
            stripped.startswith('/*') or 
            stripped.startswith('*')
        )
    
    def _is_commented_lwc(self, line: str, file_type: str) -> bool:
        """Check if line is commented in LWC files"""
        stripped = line.strip()
        
        if file_type == 'JS':
            return (
                stripped.startswith('//') or 
                stripped.startswith('/*') or 
                stripped.startswith('*')
            )
        elif file_type == 'HTML':
            return stripped.startswith('<!--')
        elif file_type == 'CSS':
            return stripped.startswith('/*') or stripped.startswith('*')
        
        return False
    
    def _is_variable_declaration(self, line: str, field_name: str) -> bool:
        """
        Check if this line is declaring a variable with the same name as the field
        This helps avoid false positives like: const Incoming = ...
        """
        # Common variable declaration patterns
        declaration_patterns = [
            rf'\b(?:const|let|var|private|public|protected|static)\s+{re.escape(field_name)}\s*[=:;]',
            rf'\b(?:String|Integer|Boolean|Decimal|Object|List|Map)\s+{re.escape(field_name)}\s*[=;]',
        ]
        
        for pattern in declaration_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        return False
    
    def _find_apex_method(self, code: str, target_line: int) -> str:
        """Find the method name containing the target line in Apex code"""
        lines = code.split('\n')
        method_pattern = re.compile(
            r'(?:public|private|protected|global)?\s+(?:static\s+)?(?:virtual\s+)?(?:override\s+)?'
            r'(?:\w+\s+)+(\w+)\s*\([^)]*\)\s*\{',
            re.IGNORECASE
        )
        
        current_method = 'Unknown'
        for i, line in enumerate(lines, 1):
            if i > target_line:
                break
            match = method_pattern.search(line)
            if match:
                current_method = match.group(1)
        
        return current_method
    
    def _find_js_function(self, code: str, target_line: int) -> str:
        """Find the function name containing the target line in JS code"""
        lines = code.split('\n')
        
        # Pattern for JS functions/methods
        function_pattern = re.compile(
            r'(?:function\s+(\w+)|(\w+)\s*\([^)]*\)\s*\{|(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)',
            re.IGNORECASE
        )
        
        current_function = 'Unknown'
        for i, line in enumerate(lines, 1):
            if i > target_line:
                break
            match = function_pattern.search(line)
            if match:
                current_function = match.group(1) or match.group(2) or match.group(3)
        
        return current_function
    
    def _extract_flow_context(self, flow_xml: str, line_num: int, field_name: str) -> str:
        """Extract context about where field is used in Flow"""
        try:
            # Try to find element type (assignment, decision, etc.)
            import json
            flow_data = json.loads(flow_xml)
            
            # Look for common flow elements
            for key in ['assignments', 'decisions', 'recordLookups', 'recordCreates', 'recordUpdates']:
                if key in flow_data:
                    return f"Flow {key.capitalize()}"
            
            return "Flow Element"
        except:
            return "Flow Element"
    
    def export_to_csv(self, filename: str = 'field_usage_analysis.csv') -> str:
        """
        Export analysis results to CSV
        
        Args:
            filename: Output CSV filename
            
        Returns:
            Path to saved CSV file
        """
        if not self.results:
            print("⚠️  No results to export")
            return ""
        
        # Convert to DataFrame
        df = pd.DataFrame(self.results)
        
        # Reorder columns for better readability
        column_order = [
            'object',
            'field',
            'component_type',
            'component_name',
            'file_type',
            'line_number',
            'method_name',
            'code_snippet',
            'is_active',
            'is_commented',
            'total_records',
            'populated_records',
            'population_percentage'
        ]
        
        df = df[column_order]
        
        # Save to CSV
        df.to_csv(filename, index=False)
        print(f"✅ Exported to {filename}")
        
        return filename
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the analysis"""
        if not self.results:
            return {}
        
        df = pd.DataFrame(self.results)
        
        return {
            'total_usages': len(self.results),
            'active_usages': len(df[df['is_active'] == True]),
            'commented_usages': len(df[df['is_commented'] == True]),
            'by_component_type': df['component_type'].value_counts().to_dict(),
            'by_file_type': df['file_type'].value_counts().to_dict(),
            'unique_fields_analyzed': len(df[['object', 'field']].drop_duplicates()),
            'unique_components': len(df['component_name'].unique())
        }
