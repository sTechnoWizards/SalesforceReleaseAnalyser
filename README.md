# Salesforce Release Impact Analyzer

AI-powered tool to analyze Salesforce release notes and identify impacted components in your org.

## Features
- ✅ Upload PDF/paste text of release notes
- ✅ AI extracts breaking changes and deprecations
- ✅ Scans ALL org metadata (Apex, LWC, Flows)
- ✅ Generates beautiful HTML impact reports
- ✅ No Salesforce governor limits
- ✅ 100% free to run

## Setup

### 1. Install Python 3.10+
```bash
python3 --version  # Should be 3.10 or higher
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Get API Keys

**Gemini API Key (Free):**
1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Copy your key

**Salesforce Credentials:**
- Username
- Password
- Security Token (Setup → My Personal Information → Reset Security Token)

### 4. Run the App
```bash
streamlit run main.py
```

## Usage

1. Upload Salesforce release notes PDF
2. Enter Salesforce credentials
3. Enter Gemini API key
4. Click "Analyze"
5. Download HTML report

## Architecture

```
PDF Upload → Gemini AI (extract breaking changes) 
                ↓
         Salesforce API (fetch ALL metadata)
                ↓
         Pattern Matcher (find impacts)
                ↓
         HTML Report Generator
```

## Cost
- **Gemini API:** FREE (1M tokens/day)
- **Hosting:** FREE (runs locally)
- **Salesforce API:** FREE (standard org access)

**Total cost: $0**

## Future Features
- [ ] Excel export
- [ ] Multi-org comparison
- [ ] Historical tracking
- [ ] Email alerts
- [ ] VS Code extension
