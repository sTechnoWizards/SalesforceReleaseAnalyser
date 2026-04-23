# Multi-Org Configuration Guide

This app now supports **multiple Salesforce orgs** with a dropdown selector to choose which org to authenticate with.

## Streamlit Cloud Secrets Format

Update your Streamlit Cloud secrets (or `.env` file) with this format:

### Option 1: Named Organizations (Recommended)

```toml
# Organization 1
ORG1_NAME = "My Production Org"
ORG1_CLIENT_ID = "YOUR_CONSUMER_KEY_FROM_ORG1"
ORG1_CLIENT_SECRET = "YOUR_CONSUMER_SECRET_FROM_ORG1"
ORG1_REDIRECT_URI = "https://salesforce-release-analyser.streamlit.app/"

# Organization 2
ORG2_NAME = "My Sandbox Org"
ORG2_CLIENT_ID = "YOUR_CONSUMER_KEY_FROM_ORG2"
ORG2_CLIENT_SECRET = "YOUR_CONSUMER_SECRET_FROM_ORG2"
ORG2_REDIRECT_URI = "https://salesforce-release-analyser.streamlit.app/"

# Add more orgs as needed (ORG3_, ORG4_, etc.)

# AI API Keys (optional)
GEMINI_API_KEY = "your_gemini_key_here"
OPENAI_API_KEY = "your_openai_key_here"
```

### Option 2: Legacy Single Org Format (Backward Compatible)

If you only have one org, you can still use the old format:

```toml
SF_CLIENT_ID = "your_consumer_key"
SF_CLIENT_SECRET = "your_consumer_secret"
SF_REDIRECT_URI = "https://salesforce-release-analyser.streamlit.app/"
```

The app will automatically detect which format you're using.

## How It Works

1. **Login Screen**: A dropdown appears if multiple orgs are configured
2. **Select Org**: Choose which Salesforce org to authenticate with
3. **Click Login**: Production or Sandbox login (based on your choice)
4. **Authenticated**: The app connects to the selected org

## Quick Setup for Your Two Orgs

Copy this template and replace with your actual credentials:

```toml
# Org 1
ORG1_NAME = "Org 1"
ORG1_CLIENT_ID = "paste_your_org1_consumer_key_here"
ORG1_CLIENT_SECRET = "paste_your_org1_consumer_secret_here"
ORG1_REDIRECT_URI = "https://salesforce-release-analyser.streamlit.app/"

# Org 2
ORG2_NAME = "Org 2"
ORG2_CLIENT_ID = "paste_your_org2_consumer_key_here"
ORG2_CLIENT_SECRET = "paste_your_org2_consumer_secret_here"
ORG2_REDIRECT_URI = "https://salesforce-release-analyser.streamlit.app/"

# Your AI keys
GEMINI_API_KEY = "your_key_here"
```

**Tip:** Change `ORG1_NAME` and `ORG2_NAME` to meaningful names like "Production", "UAT Sandbox", "Client ABC Org", etc. These names will appear in the dropdown selector.

## Important Notes

- Each Connected App must be created in the respective Salesforce org you want to analyze
- The redirect URI must match EXACTLY in both Streamlit secrets and Salesforce Connected App
- If analyzing different companies' orgs, you need separate Connected Apps from each company
- Cross-org OAuth is blocked by Salesforce (can't create Connected App in one org and authenticate to a completely different org)

## Troubleshooting

**Q: I see "OAUTH_AUTHORIZATION_BLOCKED" error**
- This means the Connected App was created in one org, but you're trying to login to a different org
- Solution: Create a separate Connected App in each target org

**Q: Dropdown doesn't appear**
- Make sure you're using the `ORG1_`, `ORG2_` prefix format (not `SF_CLIENT_ID`)
- All secrets must have matching prefixes (e.g., `ORG1_CLIENT_ID`, `ORG1_CLIENT_SECRET`, `ORG1_REDIRECT_URI`)

**Q: Want to add more orgs?**
- Just add `ORG3_`, `ORG4_`, etc. with the same pattern
- No limit on number of orgs (ORG1, ORG2, ORG3, ORG4, ORG5...)

---

**🎉 You can now switch between multiple Salesforce orgs from a single deployed app!**
