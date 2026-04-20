"""
Salesforce Metadata Client
Fetches ALL org metadata using Salesforce REST/Tooling APIs
No timeouts, no governor limits - runs on your computer!
"""

from simple_salesforce import Salesforce
import json
import requests


class SalesforceOrgScanner:
    """Client to fetch metadata from Salesforce org"""
    
    def __init__(self, username=None, password=None, security_token=None, domain='login',
                 instance_url=None, access_token=None):
        """
        Initialize Salesforce connection
        
        Args:
            username: Salesforce username (for username/password auth)
            password: Salesforce password (for username/password auth)
            security_token: Security token from email (for username/password auth)
            domain: 'login' for production, 'test' for sandbox
            instance_url: Salesforce instance URL (for OAuth, e.g., https://yourorg.my.salesforce.com)
            access_token: OAuth access token (for OAuth authentication)
        """
        try:
            # OAuth authentication (preferred - secure, no credentials stored)
            if instance_url and access_token:
                print(f"🔐 Connecting to Salesforce via OAuth...")
                print(f"   Instance: {instance_url}")
                
                self.sf = Salesforce(
                    instance_url=instance_url,
                    session_id=access_token
                )
                print("✅ Connected successfully via OAuth!")
            
            # Username/password authentication (legacy - requires security token)
            elif username and password:
                print(f"🔐 Connecting to Salesforce as {username}...")
                print(f"   Domain: {domain}.salesforce.com")
                
                self.sf = Salesforce(
                    username=username,
                    password=password,
                    security_token=security_token,
                    domain=domain
                )
                print("✅ Connected successfully!")
            
            else:
                raise ValueError("Must provide either (instance_url + access_token) or (username + password + security_token)")
            
        except Exception as e:
            print(f"\n❌ CONNECTION FAILED")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            if username:
                print(f"\n💡 Troubleshooting:")
                print(f"   - Check username: {username}")
                print(f"   - Verify password is correct")
                print(f"   - Confirm security token (Setup → Reset Security Token)")
                print(f"   - Domain should be 'login' for prod or 'test' for sandbox")
            raise
    
    def get_org_limits(self):
        """
        Get org limits (API calls, storage, data, etc.)
        Returns: Dict with limit information
        """
        try:
            print("📊 Fetching Org Limits...")
            limits = self.sf.limits()
            print(f"   ✅ Retrieved {len(limits)} limit metrics")
            return limits
        except Exception as e:
            print(f"\n❌ ERROR fetching Org Limits")
            print(f"Error: {str(e)}")
            return {}
    
    def get_org_storage(self):
        """
        Get detailed storage information
        Returns: Dict with storage details
        """
        try:
            print("💾 Fetching Storage Information...")
            # Query organization object for storage info
            query = "SELECT Id, Name, OrganizationType, InstanceName FROM Organization"
            org_info = self.sf.query(query)
            
            # Get limits for storage metrics
            limits = self.sf.limits()
            
            storage_info = {
                'organization': org_info['records'][0] if org_info['records'] else {},
                'dataStorage': limits.get('DataStorageMB', {}),
                'fileStorage': limits.get('FileStorageMB', {})
            }
            
            print(f"   ✅ Storage info retrieved")
            return storage_info
        except Exception as e:
            print(f"\n❌ ERROR fetching Storage Info")
            print(f"Error: {str(e)}")
            return {}
    
    def get_license_info(self):
        """
        Get license utilization information
        Returns: Dict with license details
        """
        try:
            print("🎫 Fetching License Information...")
            query = """
            SELECT Id, Name, Status, TotalLicenses, UsedLicenses 
            FROM UserLicense
            ORDER BY Name
            """
            result = self.sf.query_all(query)
            
            licenses = []
            for record in result['records']:
                licenses.append({
                    'name': record['Name'],
                    'status': record['Status'],
                    'total': record.get('TotalLicenses', 0),
                    'used': record.get('UsedLicenses', 0),
                    'available': record.get('TotalLicenses', 0) - record.get('UsedLicenses', 0)
                })
            
            print(f"   ✅ Found {len(licenses)} license types")
            return licenses
        except Exception as e:
            print(f"\n❌ ERROR fetching License Info")
            print(f"Error: {str(e)}")
            return []
    
    def get_permission_set_licenses(self):
        """
        Get Permission Set License utilization
        Returns: List of permission set licenses with usage info
        """
        try:
            print("🔐 Fetching Permission Set Licenses...")
            query = """
            SELECT Id, MasterLabel, DeveloperName, Status, TotalLicenses, UsedLicenses
            FROM PermissionSetLicense
            ORDER BY MasterLabel
            """
            result = self.sf.query_all(query)
            
            perm_licenses = []
            for record in result['records']:
                perm_licenses.append({
                    'name': record['MasterLabel'],
                    'devName': record.get('DeveloperName', ''),
                    'status': record.get('Status', 'Active'),
                    'total': record.get('TotalLicenses', 0),
                    'used': record.get('UsedLicenses', 0),
                    'available': record.get('TotalLicenses', 0) - record.get('UsedLicenses', 0)
                })
            
            print(f"   ✅ Found {len(perm_licenses)} permission set licenses")
            return perm_licenses
        except Exception as e:
            print(f"\n❌ ERROR fetching Permission Set Licenses")
            print(f"Error: {str(e)}")
            return []
    
    def get_all_apex_classes(self):
        """
        Fetch ALL Apex classes with full code
        Returns: List of dicts with name, code, apiVersion
        """
        try:
            print("📦 Fetching Apex Classes...")
            query = "SELECT Id, Name, Body, ApiVersion FROM ApexClass ORDER BY Name"
            
            print(f"   Running query: {query[:80]}...")
            result = self.sf.query_all(query)
            
            classes = []
            for record in result['records']:
                classes.append({
                    'name': record['Name'],
                    'code': record.get('Body', ''),  # Full code - no truncation!
                    'apiVersion': record.get('ApiVersion', 0),
                    'id': record['Id']
                })
            
            print(f"   ✅ Found {len(classes)} Apex classes")
            return classes
            
        except Exception as e:
            print(f"\n❌ ERROR fetching Apex Classes")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print(f"Query: {query}")
            print(f"Returning empty list...\n")
            return []
    
    def get_all_lwc_components(self):
        """
        Fetch ALL Lightning Web Components
        Returns: List of dicts with name, metadata
        """
        print("📦 Fetching LWC Components...")
        
        try:
            # Use Tooling API with working query
            query = """SELECT DeveloperName, IsExposed, ApiVersion, ManageableState, TargetConfigs
            FROM LightningComponentBundle
            WHERE ManageableState = 'unmanaged'"""
            
            print(f"   Using Tooling API with unmanaged filter...")
            result = self.sf.restful("tooling/query", {"q": query})
            
            if 'records' not in result:
                print(f"   ⚠️  No LWC bundles found")
                return []
            
            components = []
            all_records = result['records']
            
            # Handle pagination
            while not result['done']:
                result = self.sf.tooling.query_more(result['nextRecordsUrl'], identifier_is_url=True)
                all_records.extend(result['records'])
            
            print(f"   Found {len(all_records)} LWC components...")
            print(f"   📥 Fetching source code for each component...")
            
            for idx, record in enumerate(all_records, 1):
                comp_name = record['DeveloperName']
                print(f"   [{idx}/{len(all_records)}] {comp_name}...")
                
                # Fetch actual source code
                source_files = self.get_lwc_source(comp_name)
                
                # Build comprehensive metadata with source code
                metadata_parts = [f"LWC Component: {comp_name}"]
                metadata_parts.append(f"API Version: {record.get('ApiVersion', 'N/A')}")
                metadata_parts.append(f"Exposed: {record.get('IsExposed', False)}")
                
                if source_files:
                    metadata_parts.append("\n--- SOURCE CODE ---")
                    for filename, source in source_files.items():
                        metadata_parts.append(f"\n// File: {filename}")
                        metadata_parts.append(source)
                        metadata_parts.append(f"// End of {filename}\n")
                else:
                    metadata_parts.append("(Source code not available)")
                
                full_metadata = "\n".join(metadata_parts)
                
                components.append({
                    'name': comp_name,
                    'apiVersion': record.get('ApiVersion', ''),
                    'isExposed': record.get('IsExposed', False),
                    'targetConfigs': record.get('TargetConfigs', ''),
                    'type': 'LWC',
                    'metadata': full_metadata,
                    'source_files': source_files
                })
            
            print(f"   ✅ Found {len(components)} LWC components with source code")
            return components
        
        except Exception as e:
            print(f"\n❌ ERROR fetching LWC Components")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print(f"💡 Tip: LWC requires Tooling API access")
            print(f"Returning empty list...\n")
            return []
    
    def get_all_flows(self):
        """
        Fetch ALL Active Flows
        Returns: List of dicts with name, type, status
        """
        print("📦 Fetching Flows...")
        # Working query from user - requires Tooling API
        query = """
        SELECT Id, Definition.DeveloperName, ProcessType, Status
        FROM Flow
        WHERE Status = 'Active'
        """
        
        try:
            print(f"   Using Tooling API...")
            # Flow object requires Tooling API
            result = self.sf.restful("tooling/query", {"q": query})
            flows = []
            all_records = result['records']
            
            # Handle pagination
            while not result['done']:
                result = self.sf.tooling.query_more(result['nextRecordsUrl'], identifier_is_url=True)
                all_records.extend(result['records'])
            
            print(f"   Processing {len(all_records)} active flows...")
            print(f"   📥 Fetching full metadata for each flow...")
            
            for idx, record in enumerate(all_records, 1):
                definition = record.get('Definition', {})
                dev_name = definition.get('DeveloperName', 'Unknown') if definition else 'Unknown'
                process_type = record.get('ProcessType', 'Unknown')
                
                print(f"   [{idx}/{len(all_records)}] {dev_name}...")
                
                # Fetch full XML/metadata
                flow_xml = self.get_flow_xml(dev_name)
                
                # Build comprehensive metadata
                metadata_parts = [
                    f"Flow: {dev_name}",
                    f"Type: {process_type}",
                    f"Status: {record.get('Status', 'Active')}"
                ]
                
                if flow_xml:
                    metadata_parts.append("\n--- FLOW METADATA (JSON) ---")
                    metadata_parts.append(flow_xml)
                    metadata_parts.append("--- END FLOW METADATA ---")
                else:
                    metadata_parts.append("(Flow metadata not available)")
                
                full_metadata = "\n".join(metadata_parts)
                
                flows.append({
                    'name': dev_name,
                    'type': process_type,
                    'status': record.get('Status', 'Active'),
                    'id': record['Id'],
                    'metadata': full_metadata,
                    'flow_xml': flow_xml
                })
            
            print(f"   ✅ Found {len(flows)} active flows with full metadata")
            return flows
        
        except Exception as e:
            print(f"\n❌ ERROR fetching Flows")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print(f"Query: {query}")
            print(f"💡 Tip: Flows require Tooling API permissions")
            print(f"Returning empty list...\n")
            return []
    
    def get_all_triggers(self):
        """
        Fetch ALL Apex Triggers
        Returns: List of dicts with name, object, code
        """
        try:
            print("📦 Fetching Apex Triggers...")
            query = "SELECT Id, Name, TableEnumOrId, Body, ApiVersion FROM ApexTrigger"
            
            print(f"   Running query...")
            result = self.sf.query_all(query)
            
            triggers = []
            for record in result['records']:
                triggers.append({
                    'name': record['Name'],
                    'object': record.get('TableEnumOrId', 'Unknown'),
                    'code': record.get('Body', ''),
                    'apiVersion': record.get('ApiVersion', 0),
                    'id': record['Id']
                })
            
            print(f"   ✅ Found {len(triggers)} triggers")
            return triggers
            
        except Exception as e:
            print(f"\n❌ ERROR fetching Apex Triggers")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print(f"Query: {query}")
            print(f"Returning empty list...\n")
            return []
    
    def get_all_metadata(self):
        """
        Fetch ALL metadata from org
        This runs locally - no timeouts!
        
        Returns: Dict with all metadata
        """
        try:
            print("\n" + "="*60)
            print("🚀 Starting Org Metadata Scan")
            print("="*60 + "\n")
            
            metadata = {
                'apexClasses': self.get_all_apex_classes(),
                'apexTriggers': self.get_all_triggers(),
                'lwcComponents': self.get_all_lwc_components(),
                'flows': self.get_all_flows()
            }
            
            total = (
                len(metadata['apexClasses']) + 
                len(metadata['apexTriggers']) + 
                len(metadata['lwcComponents']) + 
                len(metadata['flows'])
            )
            
            metadata['totalComponents'] = total
            metadata['summary'] = {
                'apex': len(metadata['apexClasses']),
                'triggers': len(metadata['apexTriggers']),
                'lwc': len(metadata['lwcComponents']),
                'flows': len(metadata['flows'])
            }
            
            print("\n" + "="*60)
            print(f"✅ Scan Complete! Total: {total} components")
            print(f"   Apex Classes: {metadata['summary']['apex']}")
            print(f"   Triggers: {metadata['summary']['triggers']}")
            print(f"   LWC: {metadata['summary']['lwc']}")
            print(f"   Flows: {metadata['summary']['flows']}")
            print("="*60 + "\n")
            
            return metadata
            
        except Exception as e:
            print(f"\n" + "="*60)
            print(f"❌ METADATA SCAN FAILED")
            print(f"="*60)
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print(f"\n💡 Check the errors above for specific component issues")
            print("="*60 + "\n")
            raise
    
    def get_lwc_source(self, bundle_name):
        """
        Get full source code for a Lightning Web Component
        
        Args:
            bundle_name: Developer name of the LWC bundle (e.g., 'myComponent')
        
        Returns:
            Dict with filenames as keys and source code as values
            Example: {'myComponent.js': '...code...', 'myComponent.html': '...html...'}
        """
        try:
            print(f"\n📦 Fetching LWC source: {bundle_name}")
            
            # Step 1: Get the bundle ID
            bundle_query = f"""
                SELECT Id, DeveloperName 
                FROM LightningComponentBundle 
                WHERE DeveloperName = '{bundle_name}'
            """
            
            bundle_response = self.sf.restful("tooling/query", {"q": bundle_query})
            
            if not bundle_response.get('records'):
                print(f"   ⚠️  Bundle '{bundle_name}' not found")
                return {}
            
            bundle_id = bundle_response['records'][0]['Id']
            print(f"   ✓ Found bundle ID: {bundle_id}")
            
            # Step 2: Get all resource files for this bundle
            resource_query = f"""
                SELECT FilePath, Source 
                FROM LightningComponentResource 
                WHERE LightningComponentBundleId = '{bundle_id}'
            """
            
            resource_response = self.sf.restful("tooling/query", {"q": resource_query})
            
            source_files = {}
            for record in resource_response.get('records', []):
                file_path = record.get('FilePath', '')
                source = record.get('Source', '')
                
                # Extract filename from path (e.g., lwc/myComponent/myComponent.js -> myComponent.js)
                filename = file_path.split('/')[-1] if '/' in file_path else file_path
                source_files[filename] = source
                print(f"   ✓ Retrieved: {filename} ({len(source)} chars)")
            
            print(f"   ✅ Retrieved {len(source_files)} file(s) for {bundle_name}")
            return source_files
            
        except Exception as e:
            print(f"\n❌ ERROR fetching LWC source for '{bundle_name}'")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_flow_xml(self, flow_name):
        """
        Get full XML/metadata for a Flow
        
        Args:
            flow_name: Developer name of the flow (e.g., 'My_Auto_Flow')
        
        Returns:
            String containing the flow's metadata in readable format
        """
        try:
            print(f"\n🔄 Fetching Flow metadata: {flow_name}")
            
            # Query for active flow version with metadata
            flow_query = f"""
                SELECT Id, Definition.DeveloperName, ProcessType, Status, VersionNumber, Metadata
                FROM Flow 
                WHERE Definition.DeveloperName = '{flow_name}' 
                AND Status = 'Active'
            """
            
            flow_response = self.sf.restful("tooling/query", {"q": flow_query})
            
            if not flow_response.get('records'):
                print(f"   ⚠️  Active flow '{flow_name}' not found")
                return ""
            
            flow_record = flow_response['records'][0]
            metadata = flow_record.get('Metadata', {})
            
            # Convert metadata to formatted JSON string (readable for AI)
            if isinstance(metadata, dict):
                formatted_metadata = json.dumps(metadata, indent=2)
                print(f"   ✓ Flow type: {flow_record.get('ProcessType')}")
                print(f"   ✓ Version: {flow_record.get('VersionNumber')}")
                print(f"   ✓ Metadata size: {len(formatted_metadata)} chars")
                print(f"   ✅ Retrieved metadata for {flow_name}")
                return formatted_metadata
            else:
                # If metadata is already a string, return as-is
                print(f"   ✅ Retrieved metadata for {flow_name} (raw format)")
                return str(metadata)
            
        except Exception as e:
            print(f"\n❌ ERROR fetching Flow metadata for '{flow_name}'")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            import traceback
            traceback.print_exc()
            return ""
    
    def get_all_objects(self):
        """
        Get list of all custom and standard objects in org
        
        Returns:
            List of object names sorted alphabetically
        """
        try:
            print("📦 Fetching all objects from org...")
            
            # Query for all objects (custom and standard)
            result = self.sf.restful("sobjects/")
            
            objects = []
            for obj in result.get('sobjects', []):
                # Include custom objects and common standard objects
                if obj['createable'] or obj['queryable']:
                    objects.append({
                        'name': obj['name'],
                        'label': obj['label'],
                        'custom': obj['custom']
                    })
            
            # Sort by label
            objects.sort(key=lambda x: x['label'])
            
            print(f"   ✅ Found {len(objects)} objects")
            return objects
            
        except Exception as e:
            print(f"\n❌ ERROR fetching objects")
            print(f"Error: {str(e)}")
            return []
    
    def get_object_fields(self, object_name):
        """
        Get all fields for a specific object
        
        Args:
            object_name: API name of the object (e.g., 'Account', 'CustomObject__c')
        
        Returns:
            List of field metadata
        """
        try:
            print(f"📋 Fetching fields for {object_name}...")
            
            # Use describe to get all fields
            result = self.sf.restful(f"sobjects/{object_name}/describe/")
            
            fields = []
            for field in result.get('fields', []):
                fields.append({
                    'name': field['name'],
                    'label': field['label'],
                    'type': field['type'],
                    'custom': field.get('custom', False),
                    'calculated': field.get('calculated', False),
                    'required': not field.get('nillable', True)
                })
            
            # Sort by label
            fields.sort(key=lambda x: x['label'])
            
            print(f"   ✅ Found {len(fields)} fields")
            return fields
            
        except Exception as e:
            print(f"\n❌ ERROR fetching fields for {object_name}")
            print(f"Error: {str(e)}")
            return []
    
    def get_field_data_stats(self, object_name, field_names):
        """
        Get data population statistics for specified fields
        
        Args:
            object_name: API name of the object
            field_names: List of field API names
        
        Returns:
            Dict with field name as key and stats dict as value
        """
        try:
            print(f"📊 Fetching data statistics for {object_name} fields...")
            
            stats = {}
            
            # First, check which fields are filterable
            field_metadata = self._get_field_metadata(object_name, field_names)
            
            # Get total record count
            count_query = f"SELECT COUNT() FROM {object_name}"
            total_count_result = self.sf.query(count_query)
            total_count = total_count_result.get('totalSize', 0)
            
            # For each field, count non-null values
            for field_name in field_names:
                try:
                    # Check if field is filterable
                    metadata = field_metadata.get(field_name, {})
                    is_filterable = metadata.get('filterable', True)
                    data_type = metadata.get('dataType', 'Unknown')
                    
                    if not is_filterable:
                        print(f"   ⚠️  {field_name}: Non-filterable ({data_type}) - skipping statistics")
                        stats[field_name] = {
                            'total_count': total_count,
                            'populated_count': 0,
                            'null_count': total_count,
                            'population_pct': 0.0,
                            'filterable': False,
                            'data_type': data_type,
                            'note': f'Non-filterable field type ({data_type})'
                        }
                        continue
                    
                    # Count records where field is not null
                    populated_query = f"SELECT COUNT() FROM {object_name} WHERE {field_name} != null"
                    populated_result = self.sf.query(populated_query)
                    populated_count = populated_result.get('totalSize', 0)
                    
                    # Calculate percentage
                    population_pct = (populated_count / total_count * 100) if total_count > 0 else 0
                    
                    stats[field_name] = {
                        'total_count': total_count,
                        'populated_count': populated_count,
                        'null_count': total_count - populated_count,
                        'population_pct': round(population_pct, 2),
                        'filterable': True,
                        'data_type': data_type
                    }
                    
                except Exception as field_error:
                    error_msg = str(field_error)
                    if "can not be filtered" in error_msg:
                        print(f"   ⚠️  {field_name}: Non-filterable field - skipping statistics")
                        stats[field_name] = {
                            'total_count': total_count,
                            'populated_count': 0,
                            'null_count': total_count,
                            'population_pct': 0.0,
                            'filterable': False,
                            'note': 'Non-filterable field type'
                        }
                    else:
                        print(f"   ⚠️  Error getting stats for {field_name}: {str(field_error)[:100]}")
                        stats[field_name] = {
                            'total_count': total_count,
                            'populated_count': 0,
                            'null_count': total_count,
                            'population_pct': 0.0,
                            'error': str(field_error)
                        }
            
            return stats
            
        except Exception as e:
            print(f"\n❌ ERROR fetching field statistics")
            print(f"Error: {str(e)}")
            return {}
    
    def _get_field_metadata(self, object_name, field_names):
        """
        Get field metadata including filterability from FieldDefinition
        
        Args:
            object_name: API name of the object
            field_names: List of field API names
        
        Returns:
            Dict with field name as key and metadata as value
        """
        try:
            # Query FieldDefinition for field metadata
            field_names_str = "', '".join(field_names)
            query = f"""
                SELECT QualifiedApiName, DataType, IsFilterable
                FROM FieldDefinition 
                WHERE EntityDefinition.QualifiedApiName = '{object_name}'
                AND QualifiedApiName IN ('{field_names_str}')
            """
            
            result = self.sf.query(query)
            
            metadata = {}
            for record in result.get('records', []):
                field_name = record['QualifiedApiName']
                metadata[field_name] = {
                    'dataType': record.get('DataType', 'Unknown'),
                    'filterable': record.get('IsFilterable', True)
                }
            
            return metadata
            
        except Exception as e:
            print(f"   ⚠️  Could not fetch field metadata: {str(e)[:100]}")
            # Return empty dict, will default to assuming fields are filterable
            return {}


# ============================================================================
# OAuth 2.0 Helper Functions (Web Server Flow)
# ============================================================================

def get_authorization_url(client_id, redirect_uri, is_sandbox=False):
    """
    Generate the OAuth authorization URL for users to login
    
    Args:
        client_id: Connected App Consumer Key
        redirect_uri: Callback URL (must match Connected App setting)
        is_sandbox: True for sandbox orgs, False for production
    
    Returns:
        URL string to redirect user for authentication
    """
    base_url = "https://test.salesforce.com" if is_sandbox else "https://login.salesforce.com"
    auth_url = f"{base_url}/services/oauth2/authorize"
    
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "full refresh_token",  # Request full access and refresh token
        "prompt": "login"  # Force login screen every time
    }
    
    # Build URL with query parameters
    param_string = "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
    return f"{auth_url}?{param_string}"


def exchange_code_for_token(code, client_id, client_secret, redirect_uri, is_sandbox=False):
    """
    Exchange authorization code for access token and refresh token
    
    Args:
        code: Authorization code from OAuth callback
        client_id: Connected App Consumer Key
        client_secret: Connected App Consumer Secret
        redirect_uri: Callback URL (must match authorization request)
        is_sandbox: True for sandbox orgs
    
    Returns:
        Dict containing:
            - access_token: Use this to authenticate API calls
            - refresh_token: Use this to get new access tokens
            - instance_url: Salesforce instance URL
            - id: User identity URL
            - token_type: Usually "Bearer"
            - issued_at: Timestamp
            - signature: Response signature
    """
    token_url = "https://test.salesforce.com/services/oauth2/token" if is_sandbox else "https://login.salesforce.com/services/oauth2/token"
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Token exchange failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise


def refresh_access_token(refresh_token, client_id, client_secret, is_sandbox=False):
    """
    Refresh an expired access token using refresh token
    
    Args:
        refresh_token: Refresh token from initial authorization
        client_id: Connected App Consumer Key
        client_secret: Connected App Consumer Secret
        is_sandbox: True for sandbox orgs
    
    Returns:
        Dict containing new access_token and instance_url
    """
    token_url = "https://test.salesforce.com/services/oauth2/token" if is_sandbox else "https://login.salesforce.com/services/oauth2/token"
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Token refresh failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise


def revoke_token(token, client_id, client_secret, is_sandbox=False):
    """
    Revoke an access or refresh token (logout)
    
    Args:
        token: Access or refresh token to revoke
        client_id: Connected App Consumer Key
        client_secret: Connected App Consumer Secret
        is_sandbox: True for sandbox orgs
    """
    revoke_url = "https://test.salesforce.com/services/oauth2/revoke" if is_sandbox else "https://login.salesforce.com/services/oauth2/revoke"
    
    data = {
        "token": token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        response = requests.post(revoke_url, data=data, timeout=30)
        response.raise_for_status()
        print("✅ Token revoked successfully")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Token revocation failed: {str(e)}")


# Test function
if __name__ == "__main__":
    # Test connection
    username = input("Salesforce Username: ")
    password = input("Password: ")
    token = input("Security Token: ")
    
    client = SalesforceOrgScanner(username, password, token)
    metadata = client.get_all_metadata()
    
    print("\n📊 Summary:")
    print(f"   Apex Classes: {metadata['summary']['apex']}")
    print(f"   Triggers: {metadata['summary']['triggers']}")
    print(f"   LWC: {metadata['summary']['lwc']}")
    print(f"   Flows: {metadata['summary']['flows']}")
