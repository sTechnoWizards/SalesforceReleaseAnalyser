"""
Salesforce Release Impact Analyzer
Main Streamlit Application

Run with: streamlit run main.py
"""

import streamlit as st
import PyPDF2
import io
import json
import os
import pandas as pd
from dotenv import load_dotenv
from salesforce_client import SalesforceOrgScanner
from ai_analyzer import AIAnalyzer
from pattern_matcher import PatternMatcher
from report_generator import ReportGenerator
from field_analyzer import FieldUsageAnalyzer

# Load environment variables
load_dotenv()


# Page config
st.set_page_config(
    page_title="Salesforce Release Analyzer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    .main-header h1 {
        margin-bottom: 0.5rem;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .main-header p {
        opacity: 0.95;
        font-size: 1.1rem;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    .confidence-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
        margin-left: 8px;
    }
    .confidence-high {
        background: #d1fae5;
        color: #065f46;
    }
    .confidence-medium {
        background: #fed7aa;
        color: #9a3412;
    }
    .confidence-low {
        background: #fee2e2;
        color: #991b1b;
    }
    .metric-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .source-badge {
        background: #f3f4f6;
        color: #374151;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8em;
        font-weight: 500;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("""
<div class="main-header">
    <h1>🚀 Salesforce Release Impact Analyzer</h1>
    <p>AI-powered tool to analyze Salesforce release notes and identify impacted components in your org</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("📁 Release Notes Input")
    input_method = st.radio(
        "Choose input method:",
        ["Upload PDF", "Paste Text"]
    )
    
    release_text = ""
    
    if input_method == "Upload PDF":
        uploaded_file = st.file_uploader(
            "Upload Salesforce Release Notes PDF",
            type=['pdf'],
            help="Upload the official Salesforce release notes PDF (supports up to 60MB text content)"
        )
        
        if uploaded_file:
            # Extract PDF text with page tracking
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            release_text = ""
            page_map = {}  # Maps character positions to page numbers
            
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                start_pos = len(release_text)
                page_text = page.extract_text()
                release_text += page_text
                end_pos = len(release_text)
                page_map[page_num] = {'start': start_pos, 'end': end_pos}
            
            st.success(f"✅ PDF loaded: {len(pdf_reader.pages)} pages, {len(release_text):,} characters")
            
            # Store page map in session state
            st.session_state['page_map'] = page_map
    
    else:  # Paste Text
        release_text = st.text_area(
            "Paste release notes text:",
            height=200,
            help="Paste the Salesforce release notes content here"
        )
        
        if release_text:
            st.info(f"📝 Text length: {len(release_text):,} characters")
    
    st.divider()
    
    st.subheader("🔐 Salesforce Connection")
    
    sf_username = st.text_input(
        "Username",
        value=os.getenv('SF_USERNAME', ''),
        help="Your Salesforce username (email format)"
    )
    
    sf_password = st.text_input(
        "Password",
        type="password",
        value=os.getenv('SF_PASSWORD', ''),
        help="Your Salesforce password"
    )
    
    sf_token = st.text_input(
        "Security Token",
        type="password",
        value=os.getenv('SF_TOKEN', ''),
        help="Security token from email (Setup → Reset Security Token)"
    )
    
    sf_domain = st.selectbox(
        "Environment",
        ["login", "test"],
        index=0 if os.getenv('SF_DOMAIN', 'login') == 'login' else 1,
        help="login = Production/Developer, test = Sandbox"
    )
    
    st.divider()
    
    st.subheader("🤖 AI Configuration")
    
    gemini_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.getenv('GEMINI_API_KEY', ''),
        help="Get free key from ai.google.dev"
    )
    
    st.markdown("""
    <small>
    📌 <a href="https://ai.google.dev/" target="_blank">Get free Gemini API key</a><br>
    💡 Free tier: 1M tokens/day (enough for ~100 analyses)
    </small>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Cache management
    st.subheader("🔧 Advanced Settings")
    
    import os
    cache_exists = os.path.exists('ai_analysis_cache.json')
    if cache_exists:
        try:
            with open('ai_analysis_cache.json', 'r') as f:
                cache_data = json.load(f)
            st.success(f"✅ Cache active: {len(cache_data)} cached analysis")
        except:
            st.info("ℹ️ Cache file exists")
    else:
        st.info("ℹ️ No cached analyses yet")
    
    if st.button("🗑️ Clear Cache", help="Force fresh analysis (ignore cached results)", use_container_width=True):
        try:
            if os.path.exists('ai_analysis_cache.json'):
                os.remove('ai_analysis_cache.json')
                st.success("✅ Cache cleared! Next analysis will be fresh.")
            else:
                st.info("ℹ️ No cache to clear")
        except Exception as e:
            st.error(f"❌ Error clearing cache: {e}")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📊 Release Analysis", "🔍 Field Usage", "🏥 Org Health", "ℹ️ About"])

with tab1:
    st.header("Run Analysis")
    
    # Validation
    can_analyze = (
        release_text and
        sf_username and
        sf_password and
        sf_token and
        gemini_key
    )
    
    if not can_analyze:
        st.warning("⚠️ Please complete all configuration in the sidebar")
        st.info("""
        **Required:**
        - Release notes (PDF upload or text paste)
        - Salesforce credentials (username, password, security token)
        - Gemini API key (free from ai.google.dev)
        """)
    
    analyze_button = st.button(
        "🔍 Analyze Impact",
        type="primary",
        disabled=not can_analyze,
        use_container_width=True
    )
    
    if analyze_button:
        try:
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Connect to Salesforce
            status_text.text("🔐 Connecting to Salesforce...")
            progress_bar.progress(10)
            
            sf_client = SalesforceOrgScanner(
                sf_username,
                sf_password,
                sf_token,
                sf_domain
            )
            
            # Step 2: Fetch metadata
            status_text.text("📦 Fetching org metadata (this may take 2-3 minutes)...")
            progress_bar.progress(20)
            
            metadata = sf_client.get_all_metadata()
            
            st.success(f"✅ Fetched {metadata['totalComponents']} components from org")
            progress_bar.progress(40)
            
            # Step 3: AI comprehensive analysis of release notes
            status_text.text("🤖 AI performing comprehensive release analysis...")
            progress_bar.progress(50)
            
            ai_analyzer = AIAnalyzer(gemini_key)
            page_map = st.session_state.get('page_map', None)
            release_analysis = ai_analyzer.analyze_comprehensive_release(release_text, page_map)
            
            breaking_changes = release_analysis.get('breakingChanges', [])
            new_features = release_analysis.get('newFeatures', [])
            general_changes = release_analysis.get('generalChanges', [])
            
            if not breaking_changes and not new_features:
                st.warning("⚠️ Could not extract meaningful analysis from release notes")
                st.info("The AI may need better formatted release notes or the document may not contain structured information.")
                st.stop()
            
            st.success(f"✅ Analysis complete: {len(breaking_changes)} breaking changes, {len(new_features)} new features, {len(general_changes)} general changes")
            
            with st.expander("📋 View Full Release Analysis"):
                if release_analysis.get('summary'):
                    st.subheader("Executive Summary")
                    st.info(release_analysis['summary'])
                
                if breaking_changes:
                    st.subheader("Breaking Changes")
                    st.json(breaking_changes)
                
                if new_features:
                    st.subheader("New Features")
                    for feat in new_features:
                        st.markdown(f"**{feat['feature']}** ({feat.get('category', 'General')})")
                        st.write(feat['description'])
                
                if general_changes:
                    st.subheader("General Changes")
                    st.json(general_changes)
            
            progress_bar.progress(60)
            
            # Step 4: Pattern matching (only for breaking changes)
            status_text.text("🔍 Scanning codebase for deprecated patterns...")
            progress_bar.progress(70)
            
            impacts = []
            if breaking_changes:
                matcher = PatternMatcher(breaking_changes)
                impacts = matcher.scan_all_metadata(metadata)
            
            progress_bar.progress(90)
            
            # Step 5: Generate comprehensive report
            status_text.text("📄 Generating comprehensive HTML report...")
            
            report_gen = ReportGenerator()
            html_report = report_gen.generate_html_report(
                impacts,
                release_analysis,
                metadata['summary']
            )
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis complete!")
            
            # Display results
            st.divider()
            st.header("📊 Analysis Results")
            
            # Summary box
            if release_analysis.get('summary'):
                st.info(f"**Release Overview:** {release_analysis['summary']}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Impacted Components",
                    len(impacts),
                    delta=f"{len([i for i in impacts if i['severity'] == 'HIGH'])} HIGH priority" if impacts else None
                )
            
            with col2:
                st.metric(
                    "Breaking Changes",
                    len(breaking_changes)
                )
            
            with col3:
                st.metric(
                    "New Features",
                    len(new_features)
                )
            
            with col4:
                st.metric(
                    "Components Scanned",
                    metadata['totalComponents']
                )
            
            # New Features Display
            if new_features:
                st.subheader("🚀 New Features & Opportunities")
                
                # Group by category
                features_by_category = {}
                for feature in new_features:
                    cat = feature.get('category', 'General')
                    if cat not in features_by_category:
                        features_by_category[cat] = []
                    features_by_category[cat].append(feature)
                
                # Display by category
                for category, features in features_by_category.items():
                    with st.expander(f"📁 {category} ({len(features)} features)"):
                        for feature in features:
                            confidence = feature.get('confidence', 75)
                            conf_class = 'high' if confidence >= 85 else ('medium' if confidence >= 70 else 'low')
                            source = feature.get('source', 'Unknown')
                            
                            st.markdown(f"""
                            <div style='padding: 15px; background: white; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #3b82f6;'>
                                <h4 style='margin: 0 0 10px 0;'>
                                    ✨ {feature['feature']}
                                    <span class='confidence-badge confidence-{conf_class}'>{confidence}% confident</span>
                                    <span class='source-badge'>📍 {source}</span>
                                </h4>
                                <p style='color: #4b5563; margin-bottom: 10px;'>{feature['description']}</p>
                            """, unsafe_allow_html=True)
                            
                            if feature.get('benefits'):
                                st.markdown("**Benefits:**")
                                for benefit in feature['benefits']:
                                    st.markdown(f"- ✅ {benefit}")
                            
                            if feature.get('considerations'):
                                st.markdown("**Considerations:**")
                                for consideration in feature['considerations']:
                                    st.markdown(f"- ⚠️ {consideration}")
                            
                            if feature.get('requiresLicense'):
                                st.warning("💰 Requires additional license")
                            
                            st.markdown("</div>", unsafe_allow_html=True)
            
            # Impacted components table
            if impacts:
                st.subheader("🎯 Your Org: Impacted Components")
                
                # Convert to dataframe
                import pandas as pd
                
                df_data = []
                for impact in impacts:
                    df_data.append({
                        'Component': impact['name'],
                        'Type': impact['type'],
                        'Severity': impact['severity'],
                        'Patterns': ', '.join(impact['foundPatterns'])
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("✅ No impacted components found! Your org's components are compatible with the breaking changes.")
            
            # Download report
            st.divider()
            st.subheader("📥 Download Comprehensive Report")
            
            st.download_button(
                label="📄 Download HTML Report",
                data=html_report,
                file_name=f"salesforce_impact_report_{st.session_state.get('timestamp', 'latest')}.html",
                mime="text/html",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)

with tab2:
    st.header("🔍 Field Usage Analysis")
    st.markdown("Analyze where specific fields are used across all components in your org")
    
    # Connection validation
    can_analyze_fields = sf_username and sf_password and sf_token
    
    if not can_analyze_fields:
        st.warning("⚠️ Please enter Salesforce credentials in the sidebar to analyze field usage")
    else:
        # Initialize session state for field analysis
        if 'field_analysis_results' not in st.session_state:
            st.session_state.field_analysis_results = None
        if 'selected_objects' not in st.session_state:
            st.session_state.selected_objects = []
        if 'object_fields_map' not in st.session_state:
            st.session_state.object_fields_map = {}
        
        st.divider()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("1️⃣ Select Objects & Fields")
            
            # Fetch objects button
            if st.button("📦 Load Objects from Org", use_container_width=True):
                with st.spinner("Fetching objects..."):
                    try:
                        sf_client = SalesforceOrgScanner(
                            username=sf_username,
                            password=sf_password,
                            security_token=sf_token,
                            domain=sf_domain
                        )
                        objects = sf_client.get_all_objects()
                        st.session_state.available_objects = objects
                        st.success(f"✅ Loaded {len(objects)} objects")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            # Object selection UI
            if 'available_objects' in st.session_state:
                st.markdown("### Add Object & Fields")
                
                # Object selector
                object_options = {obj['label']: obj['name'] for obj in st.session_state.available_objects}
                selected_object_label = st.selectbox(
                    "Select Object",
                    options=list(object_options.keys()),
                    key="object_selector"
                )
                
                if selected_object_label:
                    selected_object = object_options[selected_object_label]
                    
                    # Field input
                    field_input = st.text_input(
                        "Comma-separated Field API Names",
                        placeholder="Name, Industry, Type",
                        help="Enter field API names separated by commas",
                        key="field_input"
                    )
                    
                    # Add button
                    if st.button("➕ Add Object & Fields", use_container_width=True):
                        if field_input:
                            # Parse fields
                            fields = [f.strip() for f in field_input.split(',') if f.strip()]
                            
                            # Add to map
                            if selected_object in st.session_state.object_fields_map:
                                st.session_state.object_fields_map[selected_object].extend(fields)
                                # Remove duplicates
                                st.session_state.object_fields_map[selected_object] = list(set(st.session_state.object_fields_map[selected_object]))
                            else:
                                st.session_state.object_fields_map[selected_object] = fields
                            
                            st.success(f"✅ Added {len(fields)} fields for {selected_object}")
                            st.rerun()
                        else:
                            st.warning("⚠️ Please enter at least one field")
                
                # Display selected objects and fields
                if st.session_state.object_fields_map:
                    st.markdown("### Selected for Analysis")
                    
                    for obj_name, fields in st.session_state.object_fields_map.items():
                        with st.expander(f"📦 {obj_name} ({len(fields)} fields)"):
                            for field in fields:
                                col_a, col_b = st.columns([4, 1])
                                with col_a:
                                    st.text(f"• {field}")
                                with col_b:
                                    if st.button("❌", key=f"remove_{obj_name}_{field}"):
                                        st.session_state.object_fields_map[obj_name].remove(field)
                                        if not st.session_state.object_fields_map[obj_name]:
                                            del st.session_state.object_fields_map[obj_name]
                                        st.rerun()
                    
                    if st.button("🗑️ Clear All", use_container_width=True):
                        st.session_state.object_fields_map = {}
                        st.rerun()
        
        with col2:
            st.subheader("2️⃣ Run Analysis")
            
            if not st.session_state.object_fields_map:
                st.info("👈 Add objects and fields to analyze")
            else:
                total_fields = sum(len(fields) for fields in st.session_state.object_fields_map.values())
                st.metric("Fields to Analyze", total_fields)
                
                analyze_button = st.button(
                    "🚀 Analyze Field Usage",
                    type="primary",
                    use_container_width=True
                )
                
                if analyze_button:
                    try:
                        # Create progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Connect to Salesforce
                        status_text.text("🔐 Connecting to Salesforce...")
                        progress_bar.progress(5)
                        
                        sf_client = SalesforceOrgScanner(
                            username=sf_username,
                            password=sf_password,
                            security_token=sf_token,
                            domain=sf_domain
                        )
                        
                        progress_bar.progress(10)
                        
                        # Fetch all metadata with progress updates
                        status_text.text("📦 Fetching Apex Classes...")
                        progress_bar.progress(15)
                        metadata = {'apex': sf_client.get_all_apex_classes()}
                        
                        status_text.text("⚡ Fetching Triggers...")
                        progress_bar.progress(30)
                        metadata['triggers'] = sf_client.get_all_triggers()
                        
                        status_text.text("💡 Fetching LWC Components...")
                        progress_bar.progress(45)
                        metadata['lwc'] = sf_client.get_all_lwc_components()
                        
                        status_text.text("🔄 Fetching Flows...")
                        progress_bar.progress(60)
                        metadata['flows'] = sf_client.get_all_flows()
                        
                        # Calculate summary
                        metadata['summary'] = {
                            'apex': len(metadata['apex']),
                            'triggers': len(metadata['triggers']),
                            'lwc': len(metadata['lwc']),
                            'flows': len(metadata['flows'])
                        }
                        metadata['totalComponents'] = sum(metadata['summary'].values())
                        
                        progress_bar.progress(70)
                        status_text.text(f"✅ Fetched {metadata['totalComponents']} components!")
                        
                        # Run field analysis
                        status_text.text("🔬 Analyzing field usage across all components...")
                        progress_bar.progress(75)
                        
                        analyzer = FieldUsageAnalyzer(sf_client)
                        results = analyzer.analyze_field_usage(
                            st.session_state.object_fields_map,
                            metadata
                        )
                        
                        progress_bar.progress(95)
                        
                        # Store results
                        st.session_state.field_analysis_results = results
                        st.session_state.field_analysis_summary = analyzer.get_summary()
                        
                        progress_bar.progress(100)
                        status_text.text(f"✅ Analysis complete! Found {len(results)} usages")
                        
                    except Exception as e:
                        st.error(f"❌ Error during analysis: {str(e)}")
                        st.exception(e)
        
        # Display results
        if st.session_state.field_analysis_results:
            st.divider()
            st.header("📊 Analysis Results")
            
            # Summary metrics
            summary = st.session_state.field_analysis_summary
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Usages", summary.get('total_usages', 0))
            with col2:
                st.metric("Active Usages", summary.get('active_usages', 0))
            with col3:
                st.metric("Commented Out", summary.get('commented_usages', 0))
            with col4:
                st.metric("Components", summary.get('unique_components', 0))
            
            # Breakdown by component type
            st.subheader("📂 Usage by Component Type")
            by_component = summary.get('by_component_type', {})
            if by_component:
                df_component = pd.DataFrame(list(by_component.items()), columns=['Component Type', 'Count'])
                st.bar_chart(df_component.set_index('Component Type'))
            
            # Detailed results table
            st.subheader("📋 Detailed Results")
            
            # Check if any fields had non-filterable issues
            non_filterable_note = False
            if st.session_state.field_analysis_results:
                for result in st.session_state.field_analysis_results:
                    if result.get('population_percentage', 0) == 0 and result.get('total_records', 0) > 0:
                        non_filterable_note = True
                        break
            
            if non_filterable_note:
                st.info("ℹ️ Some fields show 0% population because they are non-filterable (e.g., Long Text Area, Encrypted fields). Usage analysis is still performed for these fields.")
            
            results_df = pd.DataFrame(st.session_state.field_analysis_results)
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_object = st.multiselect(
                    "Filter by Object",
                    options=results_df['object'].unique(),
                    default=results_df['object'].unique()
                )
            with col2:
                filter_component = st.multiselect(
                    "Filter by Component Type",
                    options=results_df['component_type'].unique(),
                    default=results_df['component_type'].unique()
                )
            with col3:
                show_commented = st.checkbox("Include Commented Code", value=True)
            
            # Apply filters
            filtered_df = results_df[
                (results_df['object'].isin(filter_object)) &
                (results_df['component_type'].isin(filter_component))
            ]
            
            if not show_commented:
                filtered_df = filtered_df[filtered_df['is_commented'] == False]
            
            # Display table
            st.dataframe(
                filtered_df[[
                    'object', 'field', 'component_type', 'component_name', 
                    'file_type', 'line_number', 'method_name', 'code_snippet',
                    'is_active', 'population_percentage'
                ]],
                use_container_width=True,
                height=400
            )
            
            # Export options
            st.divider()
            st.subheader("📥 Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV export
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📄 Download as CSV",
                    data=csv,
                    file_name="field_usage_analysis.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Excel export (if openpyxl available)
                try:
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        filtered_df.to_excel(writer, sheet_name='Field Usage', index=False)
                    
                    st.download_button(
                        label="📊 Download as Excel",
                        data=buffer.getvalue(),
                        file_name="field_usage_analysis.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except ImportError:
                    st.info("💡 Install openpyxl for Excel export: pip install openpyxl")

with tab3:
    st.header("🏥 Org Health Monitoring")
    
    # Connection validation
    can_check_health = sf_username and sf_password and sf_token
    
    if not can_check_health:
        st.warning("⚠️ Please enter Salesforce credentials in the sidebar to view org health")
    else:
        check_health_button = st.button(
            "🔍 Check Org Health",
            type="primary",
            use_container_width=True
        )
        
        if check_health_button:
            try:
                with st.spinner("Connecting to Salesforce..."):
                    sf_client = SalesforceOrgScanner(
                        username=sf_username,
                        password=sf_password,
                        security_token=sf_token,
                        domain=sf_domain
                    )
                
                # Create tabs for different health metrics
                health_tab1, health_tab2, health_tab3 = st.tabs([
                    "📊 Limits", "💾 Storage", "🎫 Licenses"
                ])
                
                # Tab 1: Org Limits (SFDC-style table)
                with health_tab1:
                    st.subheader("📊 System Overview")
                    
                    with st.spinner("Fetching org limits..."):
                        limits = sf_client.get_org_limits()
                    
                    if limits:
                        # Create table data
                        import pandas as pd
                        
                        # Category mapping
                        category_map = {
                            'DailyApiRequests': 'API',
                            'DailyAsyncApexExecutions': 'ASYNC',
                            'DailyBulkV2QueryFileStorageMB': 'BULK API',
                            'DailyWorkflowEmails': 'EMAIL',
                            'DataStorageMB': 'STORAGE',
                            'FileStorageMB': 'STORAGE',
                            'HourlyAsyncReportRuns': 'ASYNC',
                            'HourlyDashboardRefreshes': 'OTHER',
                            'HourlySyncReportRuns': 'SYNC',
                            'HourlyTimeBasedWorkflow': 'OTHER',
                            'MassEmail': 'EMAIL',
                            'SingleEmail': 'EMAIL',
                            'StreamingApiConcurrentClients': 'API'
                        }
                        
                        table_data = []
                        for limit_name, limit_data in limits.items():
                            if isinstance(limit_data, dict) and 'Max' in limit_data:
                                used = limit_data['Max'] - limit_data['Remaining']
                                max_val = limit_data['Max']
                                usage_pct = (used / max_val * 100) if max_val > 0 else 0
                                
                                # Determine status
                                if usage_pct < 80:
                                    status = 'GOOD'
                                elif usage_pct < 95:
                                    status = 'WARNING'
                                else:
                                    status = 'CRITICAL'
                                
                                table_data.append({
                                    'Limit': limit_name.replace('Daily', 'Daily ').replace('Hourly', 'Hourly ').replace('MB', ' MB'),
                                    'Category': category_map.get(limit_name, 'OTHER'),
                                    'Used': used,
                                    'Max': max_val,
                                    'Usage': f"{usage_pct:.0f}%",
                                    'Status': status
                                })
                        
                        if table_data:
                            df = pd.DataFrame(table_data)
                            
                            # Display as table with styling
                            st.markdown("""
                            <style>
                            .stDataFrame {
                                width: 100%;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            # Show dataframe
                            st.dataframe(
                                df,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Limit": st.column_config.TextColumn("Limit", width="medium"),
                                    "Category": st.column_config.TextColumn("Category", width="small"),
                                    "Used": st.column_config.NumberColumn("Used", format="%d"),
                                    "Max": st.column_config.NumberColumn("Max", format="%d"),
                                    "Usage": st.column_config.TextColumn("Usage", width="small"),
                                    "Status": st.column_config.TextColumn("Status", width="small")
                                }
                            )
                    else:
                        st.error("Could not fetch org limits")
                
                # Tab 2: Storage
                with health_tab2:
                    st.subheader("Storage Usage")
                    
                    with st.spinner("Fetching storage information..."):
                        storage = sf_client.get_org_storage()
                    
                    if storage:
                        # Data Storage
                        if 'dataStorage' in storage and storage['dataStorage']:
                            st.markdown("### 💾 Data Storage")
                            data_store = storage['dataStorage']
                            used_mb = data_store['Max'] - data_store['Remaining']
                            usage_pct = (used_mb / data_store['Max'] * 100) if data_store['Max'] > 0 else 0
                            
                            cols = st.columns(3)
                            with cols[0]:
                                st.metric("Used", f"{used_mb:,.0f} MB")
                            with cols[1]:
                                st.metric("Total", f"{data_store['Max']:,.0f} MB")
                            with cols[2]:
                                st.metric("Usage", f"{usage_pct:.1f}%")
                            
                            st.progress(usage_pct / 100)
                        
                        # File Storage
                        if 'fileStorage' in storage and storage['fileStorage']:
                            st.markdown("### 📁 File Storage")
                            file_store = storage['fileStorage']
                            used_mb = file_store['Max'] - file_store['Remaining']
                            usage_pct = (used_mb / file_store['Max'] * 100) if file_store['Max'] > 0 else 0
                            
                            cols = st.columns(3)
                            with cols[0]:
                                st.metric("Used", f"{used_mb:,.0f} MB")
                            with cols[1]:
                                st.metric("Total", f"{file_store['Max']:,.0f} MB")
                            with cols[2]:
                                st.metric("Usage", f"{usage_pct:.1f}%")
                            
                            st.progress(usage_pct / 100)
                        
                        # Org Info
                        if 'organization' in storage:
                            org = storage['organization']
                            st.markdown("### 🏢 Organization Info")
                            info_cols = st.columns(2)
                            with info_cols[0]:
                                st.info(f"**Type:** {org.get('OrganizationType', 'N/A')}")
                            with info_cols[1]:
                                st.info(f"**Instance:** {org.get('InstanceName', 'N/A')}")
                    else:
                        st.error("Could not fetch storage information")
                
                # Tab 3: Licenses
                with health_tab3:
                    st.subheader("📜 License Utilization")
                    
                    with st.spinner("Fetching license information..."):
                        licenses = sf_client.get_license_info()
                    
                    if licenses:
                        # User Licenses Section
                        st.markdown("### User Licenses")
                        
                        # Filter licenses with total > 0 to avoid gaps
                        active_licenses = [lic for lic in licenses if lic['total'] > 0]
                        
                        if active_licenses:
                            # Create cards in grid layout (3 columns)
                            for i in range(0, len(active_licenses), 3):
                                cols = st.columns(3)
                                
                                for j, col in enumerate(cols):
                                    if i + j < len(active_licenses):
                                        lic = active_licenses[i + j]
                                        
                                        with col:
                                            # Calculate usage
                                            used = lic['used']
                                            total = lic['total']
                                            usage_pct = (used / total * 100) if total > 0 else 0
                                            
                                            # Determine status
                                            if usage_pct < 80:
                                                status_color = "🟢"
                                                status_text = "GOOD"
                                            elif usage_pct < 95:
                                                status_color = "🟡"
                                                status_text = "WARNING"
                                            else:
                                                status_color = "🔴"
                                                status_text = "CRITICAL"
                                            
                                            # Card container with proper contrast
                                            st.markdown(f"""
                                            <div style="border: 1px solid var(--text-color, #888); border-radius: 8px; padding: 16px; margin-bottom: 16px; background: var(--background-color, rgba(255,255,255,0.05));">
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                                    <strong style="color: var(--text-color); font-size: 14px;">{lic['name']}</strong>
                                                    <span style="font-size: 11px; color: var(--text-color);">{status_color} {status_text}</span>
                                                </div>
                                                <div style="font-size: 28px; font-weight: bold; margin-bottom: 8px; color: var(--text-color);">
                                                    {used:,} <span style="font-size: 18px; color: var(--text-color, #888);">/ {total:,}</span>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            
                                            # Progress bar
                                            st.progress(min(usage_pct / 100, 1.0))
                                            st.caption(f"{usage_pct:.1f}% utilized")
                        else:
                            st.info("No active user licenses found")
                        
                        # Permission Set Licenses Section
                        st.markdown("---")
                        st.markdown("### Permission Set Licenses")
                        
                        with st.spinner("Fetching permission set licenses..."):
                            perm_licenses = sf_client.get_permission_set_licenses()
                        
                        if perm_licenses:
                            # Filter active permission set licenses
                            active_perm_licenses = [lic for lic in perm_licenses if lic['total'] > 0]
                            
                            if active_perm_licenses:
                                # Create cards in grid layout (3 columns)
                                for i in range(0, len(active_perm_licenses), 3):
                                    cols = st.columns(3)
                                    
                                    for j, col in enumerate(cols):
                                        if i + j < len(active_perm_licenses):
                                            lic = active_perm_licenses[i + j]
                                            
                                            with col:
                                                # Calculate usage
                                                used = lic['used']
                                                total = lic['total']
                                                usage_pct = (used / total * 100) if total > 0 else 0
                                                
                                                # Determine status
                                                if usage_pct < 80:
                                                    status_color = "🟢"
                                                    status_text = "GOOD"
                                                elif usage_pct < 95:
                                                    status_color = "🟡"
                                                    status_text = "WARNING"
                                                else:
                                                    status_color = "🔴"
                                                    status_text = "CRITICAL"
                                                
                                                # Card container
                                                st.markdown(f"""
                                                <div style="border: 1px solid var(--text-color, #888); border-radius: 8px; padding: 16px; margin-bottom: 16px; background: var(--background-color, rgba(255,255,255,0.05));">
                                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                                        <strong style="color: var(--text-color); font-size: 14px;">{lic['name']}</strong>
                                                        <span style="font-size: 11px; color: var(--text-color);">{status_color} {status_text}</span>
                                                    </div>
                                                    <div style="font-size: 28px; font-weight: bold; margin-bottom: 8px; color: var(--text-color);">
                                                        {used:,} <span style="font-size: 18px; color: var(--text-color, #888);">/ {total:,}</span>
                                                    </div>
                                                </div>
                                                """, unsafe_allow_html=True)
                                                
                                                # Progress bar
                                                st.progress(min(usage_pct / 100, 1.0))
                                                st.caption(f"{usage_pct:.1f}% utilized")
                            else:
                                st.info("No active permission set licenses found")
                        else:
                            st.info("No permission set licenses available")
                        
                    else:
                        st.error("Could not fetch license information")
                        
            except Exception as e:
                st.error(f"❌ Error connecting to Salesforce: {str(e)}")
                st.info("Please check your credentials and try again")

with tab4:
    st.header("ℹ️ About")
    
    st.markdown("""
    ### Salesforce Release Impact Analyzer
    
    **Version:** 1.0.0  
    **Author:** Built with ❤️ for Salesforce developers  
    
    ---
    
    ### How It Works
    
    1. **AI Analysis:** Gemini extracts breaking changes from release notes
    2. **Metadata Scan:** Fetches ALL org components via Salesforce API
    3. **Pattern Matching:** Fast local search for deprecated code patterns
    4. **Report Generation:** Beautiful HTML report with actionable insights
    
    ---
    
    ### Tech Stack
    
    - **Python 3.10+**
    - **Streamlit** (Web UI)
    - **simple-salesforce** (Salesforce API)
    - **Google Gemini** (AI analysis)
    - **PyPDF2** (PDF processing)
    
    ---
    
    ### Benefits
    
    ✅ **100% Free** - No paid tools or hosting  
    ✅ **No Limits** - Analyze unlimited components  
    ✅ **Full Code Analysis** - Not just 800-char snippets  
    ✅ **Fast** - Results in 2-3 minutes  
    ✅ **Accurate** - AI + pattern matching  
    
    ---
    
    ### Source Code
    
    Available in: `salesforce-release-analyzer/`
    
    ---
    
    ### Support
    
    For issues or questions, check the README.md file.
    """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <small>
    Salesforce Release Impact Analyzer | 
    Powered by Google Gemini AI | 
    Free & Open Source
    </small>
</div>
""", unsafe_allow_html=True)
