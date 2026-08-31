"""
AI Analyzer using Google Gemini or OpenAI
Extracts breaking changes and analyzes component impacts
"""

import google.generativeai as genai
import json
import re
import hashlib
import os

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIAnalyzer:
    """AI-powered analyzer using Google Gemini or OpenAI"""
    
    def _load_cache(self):
        """Load analysis cache from disk"""
        import os
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                print(f"📂 Loaded {len(cache)} cached analyses from disk")
                return cache
            except Exception as e:
                print(f"⚠️ Could not load cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save analysis cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._analysis_cache, f, indent=2)
            print("💾 Cache saved to disk")
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")
    
    def _validate_critical_patterns(self, text, analysis):
        """Ensure critical patterns in text are extracted in breaking changes"""
        text_lower = text.lower()
        breaking_keywords = [bc['searchKeyword'].lower() for bc in analysis.get('breakingChanges', [])]
        
        missing_patterns = []
        for pattern in self.critical_patterns:
            if pattern.lower() in text_lower and pattern.lower() not in ' '.join(breaking_keywords):
                missing_patterns.append(pattern)
        
        if missing_patterns:
            print(f"⚠️ AI missed critical patterns: {missing_patterns}")
            print(f"🔧 Auto-adding missing patterns to breaking changes...")
            
            # Auto-add missing critical patterns
            for pattern in missing_patterns:
                analysis['breakingChanges'].append({
                    'item': f'References to {pattern}',
                    'searchKeyword': pattern,
                    'impact': f'Uses deprecated {pattern} that may be removed',
                    'alternative': 'Update to current domain structure',
                    'severity': 'HIGH',
                    'confidence': 100,
                    'source': 'Auto-detected critical pattern'
                })
            
            print(f"✅ Added {len(missing_patterns)} critical patterns to ensure detection")
        
        return analysis
    
    def __init__(self, api_key, provider='gemini', base_url=None, model_name=None):
        """
        Initialize AI with deterministic settings
        
        Args:
            api_key: API key (Gemini from ai.google.dev or OpenAI-compatible gateway)
            provider: 'gemini' or 'openai'
            base_url: Custom base URL for OpenAI-compatible gateways (e.g. https://ai-gateway-uat.healthrx.co.in/v1)
            model_name: Override default model name (e.g. 'gemini/gemini-3-flash-preview')
        """
        self.provider = provider.lower()
        self.api_key = api_key
        
        if self.provider == 'gemini':
            genai.configure(api_key=api_key)
            
            # Configure for COMPLETELY deterministic results
            generation_config = {
                'temperature': 0.0,  # Zero = 100% deterministic (no randomness)
                'top_p': 1.0,
                'top_k': 1,
            }
            
            self.model = genai.GenerativeModel(
                'gemini-2.5-flash',
                generation_config=generation_config
            )
            print("✅ Gemini AI initialized with gemini-2.5-flash")
            
        elif self.provider == 'openai':
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
            
            # Support custom base URL for OpenAI-compatible gateways
            client_kwargs = {'api_key': api_key}
            if base_url:
                client_kwargs['base_url'] = base_url
            
            self.client = OpenAI(**client_kwargs)
            self.model_name = model_name or 'gpt-5.4-pro'
            print(f"✅ OpenAI-compatible client initialized with model: {self.model_name}")
            if base_url:
                print(f"   Gateway URL: {base_url}")
        
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'gemini' or 'openai'")
        
        # Persistent disk cache (survives app restarts)
        self.cache_file = f'ai_analysis_cache_{self.provider}.json'
        self._analysis_cache = self._load_cache()
        
        # Critical patterns that must ALWAYS be extracted
        self.critical_patterns = [
            'force.com',
            'my.salesforce.com', 
            'visualforce.com',
            'enhanced domain',
            'deprecated',
            'removed',
            'no longer supported'
        ]
        
        print(f"✅ AI Analyzer ready with persistent cache ({self.provider})")
    
    def _generate_response(self, prompt):
        """
        Generate AI response using configured provider
        
        Args:
            prompt: Text prompt for AI
            
        Returns:
            Response text string
        """
        if self.provider == 'gemini':
            response = self.model.generate_content(prompt)
            return response.text
        
        elif self.provider == 'openai':
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a Salesforce release notes analyzer. Provide accurate, structured analysis in JSON format. Return ONLY valid JSON, no markdown."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def analyze_comprehensive_release(self, release_notes_text, page_map=None):
        """
        Comprehensive release notes analysis with chunked processing for large documents
        
        Args:
            release_notes_text: Full text of release notes
            page_map: Dict mapping text positions to page numbers
            
        Returns:
            Dict with summary, breaking_changes, new_features, general_changes (with confidence scores)
        """
        print("\n" + "="*60)
        print("🤖 AI COMPREHENSIVE ANALYSIS STARTING")
        print("="*60)
        
        # Create cache key from FULL content hash
        cache_key = hashlib.md5(release_notes_text.encode()).hexdigest()
        
        total_chars = len(release_notes_text)
        chunk_size = 100000  # 100K chars per chunk (~25K tokens, cost-effective)
        num_chunks = max(1, (total_chars + chunk_size - 1) // chunk_size)
        
        print(f"📊 Analysis Info:")
        print(f"   - Total text length: {total_chars:,} chars")
        print(f"   - Chunk size: {chunk_size:,} chars")
        print(f"   - Chunks to process: {num_chunks}")
        print(f"   - Cache key: {cache_key[:20]}...")
        
        # Check cache first for consistency
        if cache_key in self._analysis_cache:
            print("\n🎯 Using cached analysis (ensures consistency across runs)")
            return self._analysis_cache[cache_key]
        
        print("\n🤖 AI performing comprehensive release analysis...")
        
        # Process in chunks
        all_breaking_changes = []
        all_new_features = []
        all_general_changes = []
        all_recommendations = []
        summaries = []
        all_sections = []
        
        for i in range(num_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, total_chars)
            chunk_text = release_notes_text[start:end]
            
            print(f"\n   📄 Processing chunk {i+1}/{num_chunks} ({start:,}-{end:,} chars, {len(chunk_text):,} chars)")
            
            chunk_analysis = self._analyze_chunk(chunk_text, i+1, num_chunks)
            
            if chunk_analysis:
                all_breaking_changes.extend(chunk_analysis.get('breakingChanges', []))
                all_new_features.extend(chunk_analysis.get('newFeatures', []))
                all_general_changes.extend(chunk_analysis.get('generalChanges', []))
                all_recommendations.extend(chunk_analysis.get('recommendations', []))
                if chunk_analysis.get('summary'):
                    summaries.append(chunk_analysis['summary'])
                all_sections.extend(chunk_analysis.get('metadata', {}).get('sectionsAnalyzed', []))
        
        # Deduplicate by searchKeyword/feature name
        breaking_changes = self._deduplicate_items(all_breaking_changes, 'searchKeyword')
        new_features = self._deduplicate_items(all_new_features, 'feature')
        general_changes = self._deduplicate_items(all_general_changes, 'change')
        recommendations = list(set(all_recommendations))
        
        # Merge summary
        summary = summaries[0] if summaries else "Unable to analyze release notes"
        if len(summaries) > 1:
            summary = " ".join(summaries[:2])  # Combine first two chunk summaries
        
        analysis = {
            "summary": summary,
            "breakingChanges": breaking_changes,
            "newFeatures": new_features,
            "generalChanges": general_changes,
            "recommendations": recommendations,
            "metadata": {
                "sectionsAnalyzed": list(set(all_sections)),
                "coverageEstimate": "100%",
                "chunksProcessed": num_chunks,
                "totalCharsAnalyzed": total_chars
            }
        }
        
        print(f"\n   ✅ MERGED RESULTS:")
        print(f"   ✅ Breaking Changes: {len(breaking_changes)}")
        print(f"   ✅ New Features: {len(new_features)}")
        print(f"   ✅ General Changes: {len(general_changes)}")
        
        # Validate critical patterns
        print("   🔍 Validating critical patterns...")
        analysis = self._validate_critical_patterns(release_notes_text[:500000], analysis)
        
        # Cache the results for consistency
        self._analysis_cache[cache_key] = analysis
        self._save_cache()
        print("💾 Results cached for consistency (saved to disk)")
        
        return analysis
    
    def _deduplicate_items(self, items, key_field):
        """Remove duplicates based on a key field"""
        seen = set()
        unique = []
        for item in items:
            key = item.get(key_field, '').lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(item)
            elif not key:
                unique.append(item)
        return unique
    
    def _analyze_chunk(self, text, chunk_num, total_chunks):
        """Analyze a single chunk of release notes text"""
        
        chunk_context = f"(Chunk {chunk_num} of {total_chunks})" if total_chunks > 1 else ""
        
        prompt = f"""
You are analyzing Salesforce release notes {chunk_context}. Extract ALL significant information comprehensively and CONSISTENTLY.

CRITICAL: You must extract the SAME information every time you analyze this document. Do not randomly omit items.

IMPORTANT: For EVERY item, include:
1. "confidence" score (0-100) - how certain you are this information is in the document
2. "source" - section name or context where found (e.g., "Security & Identity", "Automation")

Extract and categorize EVERYTHING you find:

1. **EXECUTIVE SUMMARY**: 2-3 sentence overview
2. **BREAKING CHANGES**: ALL deprecated/removed/changed functionality (MUST extract ALL, aim for 10-30 items)
3. **NEW FEATURES**: ALL new capabilities (MUST extract ALL, aim for 20-50 features)
4. **GENERAL CHANGES**: ALL updates, enhancements, improvements (MUST extract ALL, aim for 10-30 items)
5. **RECOMMENDATIONS**: Best practices for adoption

CONSISTENCY RULE: Always extract ALL items you find. Do not randomly skip items between runs.

**Breaking Changes Format:**
{{
  "item": "Feature name",
  "searchKeyword": "Exact text/API to search in code",
  "impact": "What breaks and why",
  "alternative": "What to use instead",
  "severity": "HIGH/MEDIUM/LOW",
  "confidence": 95,
  "source": "Section name where found"
}}

**New Features Format:**
{{
  "feature": "Feature name",
  "category": "Analytics/AI/Security/Mobile/Automation/Sales/Service/Commerce/etc",
  "description": "What it does",
  "benefits": ["Benefit 1", "Benefit 2", "Benefit 3"],
  "considerations": ["Consideration 1", "Consideration 2"],
  "useCases": ["Use case 1", "Use case 2"],
  "requiresLicense": true/false,
  "confidence": 90,
  "source": "Section name"
}}

**General Changes Format:**
{{
  "change": "Change description",
  "category": "Category",
  "impact": "Potential impact on org",
  "actionRequired": true/false,
  "confidence": 85,
  "source": "Section name"
}}

CONFIDENCE SCORING GUIDE:
- 95-100: Explicitly stated with full details
- 85-94: Clearly mentioned, some details inferred
- 75-84: Mentioned but limited context
- 60-74: Partially mentioned or inferred
- Below 60: Best guess based on patterns

Return ONLY valid JSON, no markdown:
{{
  "summary": "Executive summary text",
  "breakingChanges": [...],
  "newFeatures": [...],
  "generalChanges": [...],
  "recommendations": ["Rec 1", "Rec 2"],
  "metadata": {{
    "sectionsAnalyzed": ["Section 1", "Section 2"],
    "coverageEstimate": "percentage analyzed"
  }}
}}

Release Notes Text {chunk_context}:
{text}
"""
        
        try:
            print(f"   🤖 Sending chunk {chunk_num} to {self.provider.title()} AI...")
            print(f"   📝 Prompt length: {len(prompt):,} chars")
            
            response_text = self._generate_response(prompt)
            
            print(f"   ✅ Received response for chunk {chunk_num}")
            print(f"   📄 Response length: {len(response_text):,} chars")
            
            result_text = response_text.strip()
            
            # Log first 200 chars for debugging
            print(f"   🔍 Response preview: {result_text[:200]}...")
            
            # Clean up markdown code blocks
            result_text = re.sub(r'```json\s*', '', result_text)
            result_text = re.sub(r'```\s*$', '', result_text)
            result_text = result_text.strip()
            
            print("   🔄 Parsing JSON response...")
            
            # Parse JSON
            analysis = json.loads(result_text)
            
            print(f"   ✅ Chunk {chunk_num} - Breaking Changes: {len(analysis.get('breakingChanges', []))}")
            print(f"   ✅ Chunk {chunk_num} - New Features: {len(analysis.get('newFeatures', []))}")
            print(f"   ✅ Chunk {chunk_num} - General Changes: {len(analysis.get('generalChanges', []))}")
            
            return analysis
        
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON PARSING ERROR in chunk {chunk_num}")
            print(f"Error: {str(e)}")
            print(f"Response preview: {response_text[:500] if 'response_text' in dir() else 'N/A'}")
            return self._get_empty_analysis()
            
        except Exception as e:
            print(f"\n❌ ERROR in chunk {chunk_num}: {type(e).__name__}: {str(e)}")
            return self._get_empty_analysis()
    
    def clear_cache(self):
        """Clear analysis cache (both memory and disk)"""
        import os
        self._analysis_cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            print("🗑️ Analysis cache cleared")
        else:
            print("ℹ️ No cache file to clear")
    
    def _get_empty_analysis(self):
        """Return empty analysis structure"""
        return {
            "summary": "Unable to analyze release notes",
            "breakingChanges": [],
            "newFeatures": [],
            "generalChanges": [],
            "recommendations": []
        }
    
    def extract_breaking_changes(self, release_notes_text):
        """
        Extract ONLY breaking changes (backward compatibility method)
        
        Args:
            release_notes_text: Full text of release notes
            
        Returns:
            List of breaking changes
        """
        analysis = self.analyze_comprehensive_release(release_notes_text)
        return analysis.get('breakingChanges', [])
    
    def analyze_component_impact(self, component_name, component_code, breaking_changes):
        """
        Analyze if a component is impacted by breaking changes
        (Optional - we can use fast local pattern matching instead)
        
        Args:
            component_name: Name of component
            component_code: Full code of component
            breaking_changes: List of breaking changes
            
        Returns:
            Impact analysis result
        """
        # Create summary of breaking changes
        changes_summary = "\n".join([
            f"- {c['searchKeyword']}: {c['impact']}"
            for c in breaking_changes
        ])
        
        # Truncate code to 5000 chars (Gemini can handle it, unlike Salesforce!)
        code_snippet = component_code[:5000]
        
        prompt = f"""
Component: {component_name}

Code (first 5000 chars):
```
{code_snippet}
```

Breaking Changes to Check:
{changes_summary}

Analyze if this component uses any of the deprecated features.

Return ONLY valid JSON (no markdown):
{{
  "impacted": true/false,
  "foundPatterns": ["pattern1", "pattern2"],
  "severity": "HIGH/MEDIUM/LOW",
  "lineNumbers": [12, 45],
  "recommendation": "Specific action needed"
}}
"""
        
        try:
            response_text = self._generate_response(prompt)
            result_text = response_text.strip()
            
            # Clean up (in case AI adds markdown)
            result_text = re.sub(r'```json\s*', '', result_text)
            result_text = re.sub(r'```\s*$', '', result_text)
            
            return json.loads(result_text)
        
        except Exception as e:
            print(f"   ⚠️  Error analyzing {component_name}: {e}")
            return None


# Test function
if __name__ == "__main__":
    api_key = input("Enter Gemini API Key: ")
    
    analyzer = AIAnalyzer(api_key)
    
    # Test with sample release notes
    sample_notes = """
    Salesforce Winter '26 Release Notes
    
    Breaking Changes:
    - The @track decorator for Lightning Web Components is deprecated.
      Use reactive properties instead.
    - UserInfo.getSessionId() will be removed in Summer '26.
      Use Named Credentials for authentication.
    """
    
    changes = analyzer.extract_breaking_changes(sample_notes)
    
    print("\n📋 Extracted Changes:")
    print(json.dumps(changes, indent=2))
