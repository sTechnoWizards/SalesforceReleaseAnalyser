"""
HTML Report Generator
Creates beautiful, professional impact analysis reports
"""

from datetime import datetime
import json


class ReportGenerator:
    """Generate HTML impact reports"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def generate_html_report(self, impacts, release_analysis, metadata_summary):
        """
        Generate comprehensive HTML report
        
        Args:
            impacts: List of impacted components
            release_analysis: Dict with summary, breaking_changes, new_features, etc.
            metadata_summary: Dict with org summary
            
        Returns:
            HTML string
        """
        # Extract components from comprehensive analysis
        breaking_changes = release_analysis.get('breakingChanges', [])
        new_features = release_analysis.get('newFeatures', [])
        general_changes = release_analysis.get('generalChanges', [])
        summary = release_analysis.get('summary', 'No summary available')
        recommendations = release_analysis.get('recommendations', [])
        # Calculate stats
        total_impacted = len(impacts)
        high_severity = len([i for i in impacts if i.get('severity') == 'HIGH'])
        medium_severity = len([i for i in impacts if i.get('severity') == 'MEDIUM'])
        low_severity = len([i for i in impacts if i.get('severity') == 'LOW'])
        
        by_type = {}
        for impact in impacts:
            comp_type = impact['type']
            by_type[comp_type] = by_type.get(comp_type, 0) + 1
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Salesforce Release Impact Analysis Report</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            border: 2px solid #bfdbfe;
        }}
        
        .stat-value {{
            font-size: 3em;
            font-weight: 800;
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .stat-label {{
            color: #1e40af;
            font-weight: 600;
            margin-top: 5px;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #1e3a8a;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 12px;
            margin-bottom: 25px;
            font-weight: 700;
        }}
        
        .breaking-changes {{
            background: #fef3c7;
            border-left: 5px solid #f59e0b;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        
        .breaking-changes h3 {{
            color: #92400e;
            margin-bottom: 15px;
        }}
        
        .change-item {{
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 3px solid #f59e0b;
        }}
        
        .change-keyword {{
            font-family: 'Courier New', monospace;
            background: #1e293b;
            color: #22d3ee;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        thead {{
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
            color: white;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        tbody tr:hover {{
            background: #f8fafc;
        }}
        
        .severity-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 700;
            text-transform: uppercase;
        }}
        
        .severity-HIGH {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .severity-MEDIUM {{
            background: #fed7aa;
            color: #9a3412;
        }}
        
        .severity-LOW {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .type-badge {{
            background: #f3f4f6;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.85em;
            color: #374151;
            font-weight: 600;
        }}
        
        .patterns-list {{
            margin: 5px 0;
        }}
        
        .pattern-tag {{
            display: inline-block;
            background: #1e293b;
            color: #22d3ee;
            padding: 3px 10px;
            border-radius: 4px;
            margin: 2px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }}
        
        .recommendation {{
            color: #059669;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .confidence-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            margin-left: 8px;
        }}
        
        .confidence-high {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .confidence-medium {{
            background: #fed7aa;
            color: #9a3412;
        }}
        
        .confidence-low {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .source-badge {{
            background: #f3f4f6;
            color: #374151;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75em;
            font-weight: 500;
            margin-left: 6px;
        }}
        
        .footer {{
            background: #f8fafc;
            padding: 30px;
            text-align: center;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
        }}
        
        .no-impacts {{
            background: #d1fae5;
            border: 2px solid #059669;
            color: #065f46;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            font-size: 1.2em;
        }}
        
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Salesforce Release Impact Analysis</h1>
            <p>Generated on {self.timestamp}</p>
        </div>
        
        <div class="content">
            <!-- Summary Stats -->
            <div class="summary-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_impacted}</div>
                    <div class="stat-label">Impacted Components</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{high_severity}</div>
                    <div class="stat-label">High Priority</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(breaking_changes)}</div>
                    <div class="stat-label">Breaking Changes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{metadata_summary.get('apex', 0)}</div>
                    <div class="stat-label">Apex Classes Scanned</div>
                </div>
            </div>
"""
        
        # Breaking Changes Section
        if breaking_changes:
            html += """
            <div class="section">
                <h2 class="section-title">⚠️ Breaking Changes Detected</h2>
                <div class="breaking-changes">
                    <h3>Deprecated Features & APIs</h3>
"""
            for change in breaking_changes:
                html += f"""
                    <div class="change-item">
                        <strong>{change['item']}</strong><br>
                        <span class="change-keyword">{change['searchKeyword']}</span><br>
                        <small>Impact: {change['impact']}</small><br>
                        <small style="color: #059669;">✅ Alternative: {change['alternative']}</small>
                    </div>
"""
            html += """
                </div>
            </div>
"""
        
        # Impacted Components Table
        if impacts:
            html += """
            <div class="section">
                <h2 class="section-title">🎯 Impacted Components</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Component Name</th>
                            <th>Type</th>
                            <th>Deprecated Patterns</th>
                            <th>Severity</th>
                            <th>Recommendation</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for impact in sorted(impacts, key=lambda x: (x['severity'], x['name'])):
                patterns_html = ''.join([
                    f'<span class="pattern-tag">{p}</span>'
                    for p in impact['foundPatterns']
                ])
                
                # FIX: Get recommendations as list, not string
                recommendations_list = impact.get('recommendations', ['Review and update'])
                if isinstance(recommendations_list, str):
                    # If it's a single string, wrap in list
                    recommendations_list = [recommendations_list]
                recommendations = '<br>'.join(recommendations_list)
                
                html += f"""
                        <tr>
                            <td><strong>{impact['name']}</strong></td>
                            <td><span class="type-badge">{impact['type']}</span></td>
                            <td class="patterns-list">{patterns_html}</td>
                            <td><span class="severity-badge severity-{impact['severity']}">{impact['severity']}</span></td>
                            <td class="recommendation">{recommendations}</td>
                        </tr>
"""
            html += """
                    </tbody>
                </table>
            </div>
"""
        else:
            html += """
            <div class="section">
                <div class="no-impacts">
                    ✅ No Impacted Components Found!<br>
                    <small>Your org appears to be compatible with the new release.</small>
                </div>
            </div>
"""
        
        # Release Summary Section
        html += f"""
            <div class="section">
                <h2 class="section-title">📝 Release Summary</h2>
                <div style="background: #f0f9ff; border-left: 5px solid #3b82f6; padding: 20px; border-radius: 8px;">
                    <p style="font-size: 1.1em; line-height: 1.8; color: #1e40af;">{summary}</p>
                </div>
            </div>
"""
        
        # New Features Section
        if new_features:
            html += """
            <div class="section">
                <h2 class="section-title">🚀 New Features & Opportunities</h2>
"""
            for feature in new_features:
                confidence = feature.get('confidence', 75)
                conf_class = 'high' if confidence >= 85 else ('medium' if confidence >= 70 else 'low')
                source = feature.get('source', 'Unknown Section')
                
                benefits_html = ''.join([f'<li style="color: #059669;">✅ {b}</li>' for b in feature.get('benefits', [])])
                considerations_html = ''.join([f'<li style="color: #d97706;">⚠️ {c}</li>' for c in feature.get('considerations', [])])
                use_cases_html = ''.join([f'<li>{u}</li>' for u in feature.get('useCases', [])])
                
                license_badge = ''
                if feature.get('requiresLicense'):
                    license_badge = '<span style="background: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-size: 0.85em; margin-left: 10px;">💰 Requires License</span>'
                
                html += f"""
                <div style="background: white; border: 2px solid #e5e7eb; border-radius: 12px; padding: 25px; margin-bottom: 20px;">
                    <h3 style="color: #1e3a8a; margin-bottom: 10px;">
                        {feature['feature']}
                        <span style="background: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 6px; font-size: 0.85em; margin-left: 10px;">{feature.get('category', 'General')}</span>
                        <span class="confidence-badge confidence-{conf_class}">{confidence}% confident</span>
                        <span class="source-badge">📍 {source}</span>
                        {license_badge}
                    </h3>
                    <p style="color: #4b5563; margin-bottom: 15px;">{feature['description']}</p>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <h4 style="color: #059669; margin-bottom: 10px;">Benefits</h4>
                            <ul style="margin-left: 20px;">{benefits_html}</ul>
                        </div>
                        <div>
                            <h4 style="color: #d97706; margin-bottom: 10px;">Considerations</h4>
                            <ul style="margin-left: 20px;">{considerations_html}</ul>
                        </div>
                    </div>
                    
                    {f'<div style="margin-top: 15px;"><h4 style="color: #6366f1; margin-bottom: 10px;">Use Cases</h4><ul style="margin-left: 20px; color: #4b5563;">{use_cases_html}</ul></div>' if use_cases_html else ''}
                </div>
"""
            html += """
            </div>
"""
        
        # Breaking Changes Section (Enhanced)
        if breaking_changes:
            html += """
            <div class="section">
                <h2 class="section-title">⚠️ Breaking Changes & Deprecations</h2>
                <div class="breaking-changes">
                    <h3>Action Required: Update Your Code</h3>
"""
            for change in breaking_changes:
                confidence = change.get('confidence', 75)
                conf_class = 'high' if confidence >= 85 else ('medium' if confidence >= 70 else 'low')
                source = change.get('source', 'Unknown Section')
                
                severity_color = {
                    'HIGH': '#dc2626',
                    'MEDIUM': '#f59e0b',
                    'LOW': '#3b82f6'
                }.get(change.get('severity', 'MEDIUM'), '#f59e0b')
                
                html += f"""
                    <div class="change-item">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                            <strong style="font-size: 1.1em; color: #1e293b;">{change['item']}</strong>
                            <div>
                                <span style="background: {severity_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 700;">{change.get('severity', 'MEDIUM')}</span>
                                <span class="confidence-badge confidence-{conf_class}">{confidence}%</span>
                                <span class="source-badge">📍 {source}</span>
                            </div>
                        </div>
                        <div style="background: #1e293b; padding: 8px 12px; border-radius: 6px; margin: 10px 0;">
                            <code style="color: #22d3ee; font-family: 'Courier New', monospace;">{change['searchKeyword']}</code>
                        </div>
                        <p style="color: #dc2626; margin: 10px 0;"><strong>Impact:</strong> {change['impact']}</p>
                        <p style="color: #059669; margin: 10px 0;"><strong>✅ Alternative:</strong> {change['alternative']}</p>
                    </div>
"""
            html += """
                </div>
            </div>
"""
        
        # General Changes Section
        if general_changes:
            html += """
            <div class="section">
                <h2 class="section-title">📋 General Changes & Updates</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead style="background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white;">
                        <tr>
                            <th style="padding: 15px; text-align: left;">Change</th>
                            <th style="padding: 15px; text-align: left;">Category</th>
                            <th style="padding: 15px; text-align: left;">Impact</th>
                            <th style="padding: 15px; text-align: center;">Action Required</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for change in general_changes:
                action_badge = '🔴 Yes' if change.get('actionRequired') else '✅ No'
                action_color = '#fee2e2' if change.get('actionRequired') else '#d1fae5'
                
                html += f"""
                        <tr>
                            <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;"><strong>{change['change']}</strong></td>
                            <td style="padding: 15px; border-bottom: 1px solid #e5e7eb;">
                                <span style="background: #f3f4f6; padding: 4px 10px; border-radius: 6px; font-size: 0.85em;">{change.get('category', 'General')}</span>
                            </td>
                            <td style="padding: 15px; border-bottom: 1px solid #e5e7eb; color: #4b5563;">{change['impact']}</td>
                            <td style="padding: 15px; border-bottom: 1px solid #e5e7eb; text-align: center;">
                                <span style="background: {action_color}; padding: 6px 12px; border-radius: 6px; font-size: 0.9em;">{action_badge}</span>
                            </td>
                        </tr>
"""
            html += """
                    </tbody>
                </table>
            </div>
"""
        
        # Impacted Components Table
        if impacts:
            html += """
            <div class="section">
                <h2 class="section-title">🎯 Your Org: Impacted Components</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Component Name</th>
                            <th>Type</th>
                            <th>Deprecated Patterns</th>
                            <th>Severity</th>
                            <th>Recommendation</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for impact in sorted(impacts, key=lambda x: (x['severity'], x['name'])):
                patterns_html = ''.join([
                    f'<span class="pattern-tag">{p}</span>'
                    for p in impact['foundPatterns']
                ])
                
                # FIX: Ensure recommendations is a list
                recommendations_list = impact.get('recommendations', ['Review and update'])
                if isinstance(recommendations_list, str):
                    recommendations_list = [recommendations_list]
                recommendations_html = '<br>'.join(recommendations_list)
                
                html += f"""
                        <tr>
                            <td><strong>{impact['name']}</strong></td>
                            <td><span class="type-badge">{impact['type']}</span></td>
                            <td class="patterns-list">{patterns_html}</td>
                            <td><span class="severity-badge severity-{impact['severity']}">{impact['severity']}</span></td>
                            <td class="recommendation">{recommendations_html}</td>
                        </tr>
"""
            html += """
                    </tbody>
                </table>
            </div>
"""
        else:
            html += """
            <div class="section">
                <div class="no-impacts">
                    ✅ No Impacted Components Found!<br>
                    <small>Your org's current components are compatible with the breaking changes in this release.</small>
                </div>
            </div>
"""
        
        # Recommendations Section
        if recommendations:
            # Ensure recommendations is a list, not a string
            if isinstance(recommendations, str):
                # If it's a string, treat it as a single recommendation
                recommendations = [recommendations]
            
            html += """
            <div class="section">
                <h2 class="section-title">💡 Recommendations & Best Practices</h2>
                <div style="background: linear-gradient(135deg, #f0fdf4, #dcfce7); border-left: 5px solid #059669; padding: 25px; border-radius: 8px;">
                    <ul style="margin-left: 20px; line-height: 2;">
"""
            for rec in recommendations:
                # Ensure each recommendation is treated as a single item, not iterated character by character
                if rec and isinstance(rec, str):
                    html += f'                        <li style="color: #065f46; font-size: 1.05em;"><strong>{rec}</strong></li>\n'
            html += """
                    </ul>
                </div>
            </div>
"""
        
        html += f"""
        </div>
        
        <div class="footer">
            <p><strong>Salesforce Release Impact Analyzer</strong></p>
            <p>Org Components Scanned: {metadata_summary.get('apex', 0)} Apex • {metadata_summary.get('triggers', 0)} Triggers • {metadata_summary.get('lwc', 0)} LWC • {metadata_summary.get('flows', 0)} Flows</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Comprehensive report generated by AI-powered analysis tool</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def save_report(self, html, filename='salesforce_impact_report.html'):
        """Save report to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ Report saved: {filename}")
        return filename
