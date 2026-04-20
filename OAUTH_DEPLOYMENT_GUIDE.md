# 🚀 Deployment Guide: OAuth 2.0 + Multi-AI Setup

Complete guide to deploy Salesforce Release Analyzer with secure OAuth authentication and AI provider choice (Gemini or OpenAI).

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Salesforce Connected App Setup](#salesforce-connected-app-setup)
4. [Deployment Options](#deployment-options)
5. [Testing Locally](#testing-locally)
6. [Troubleshooting](#troubleshooting)

---

## Overview

This app now supports:
- **OAuth 2.0** - Secure authentication, no password storage
- **Multi-AI** - Choose between Google Gemini or OpenAI ChatGPT
- **Per-user authentication** - Each user logs in with their own Salesforce credentials

---

## Prerequisites

### 1. Get AI API Keys

**Option A: Google Gemini (Free tier available)**
1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create a new key (free tier: 60 requests/minute)
4. Save the key

**Option B: OpenAI (Paid)**
1. Go to https://platform.openai.com/
2. Create account or login
3. Navigate to API Keys section
4. Create a new secret key
5. Save the key (starts with `sk-...`)

### 2. Salesforce Admin Access

You need Salesforce admin privileges to create a Connected App.

---

## Salesforce Connected App Setup

### Step 1: Create Connected App

1. Login to your Salesforce org
2. Navigate to **Setup** → Search for **"App Manager"**
3. Click **"New Connected App"**
4. Fill in basic information:
   - **Connected App Name**: `Salesforce Release Analyzer`
   - **API Name**: `Salesforce_Release_Analyzer`
   - **Contact Email**: Your email

### Step 2: Configure OAuth Settings

1. Check **"Enable OAuth Settings"**

2. **Callback URL**: Enter your app's redirect URI:
   - For Streamlit Cloud: `https://your-app-name.streamlit.app/`
   - For local testing: `http://localhost:8501/`
   - For custom domain: `https://yourdomain.com/`

3. **Selected OAuth Scopes**: Add these scopes:
   - `Access the identity URL service (id, profile, email, address, phone)`
   - `Manage user data via APIs (api)`
   - `Perform requests at any time (refresh_token, offline_access)`
   - `Access unique user identifiers (openid)`
   - `Full access (full)`

4. Click **Save**
5. Click **Continue**

### Step 3: Get Client Credentials

1. On the Connected App detail page, click **"Manage Consumer Details"**
2. Verify your identity (email verification code)
3. Copy these values:
   - **Consumer Key** (this is your Client ID)
   - **Consumer Secret** (this is your Client Secret)
4. Store them securely - you'll need them for deployment

### Step 4: Enable App (Optional but Recommended)

1. Back on the Connected App page
2. Click **"Manage"**
3. Click **"Edit Policies"**
4. **Permitted Users**: Choose your preference:
   - `Admin approved users are pre-authorized` (recommended for internal use)
   - `All users may self-authorize` (for wider access)
5. Click **Save**

---

## Deployment Options

### Option 1: Streamlit Community Cloud (Free & Recommended)

#### 4.1 Push Code to GitHub

```bash
# Navigate to your project
cd /path/to/salesforce-release-analyzer

# Initialize git (if not already done)
git init
git add .
git commit -m "Add OAuth and multi-AI support"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

#### 4.2 Deploy to Streamlit Cloud

1. Go to https://streamlit.io/cloud
2. Click **"New app"**
3. Connect your GitHub repository
4. Select:
   - **Repository**: `YOUR_USERNAME/YOUR_REPO`
   - **Branch**: `main`
   - **Main file path**: `main.py`

#### 4.3 Configure Secrets

1. In Streamlit Cloud app settings, go to **"Secrets"**
2. Add the following in TOML format:

```toml
# Salesforce Connected App Credentials
SF_CLIENT_ID = "YOUR_CONSUMER_KEY_HERE"
SF_CLIENT_SECRET = "YOUR_CONSUMER_SECRET_HERE"
SF_REDIRECT_URI = "https://your-app-name.streamlit.app/"

# AI API Keys (add one or both)
GEMINI_API_KEY = "YOUR_GEMINI_KEY_HERE"  # Optional
OPENAI_API_KEY = "YOUR_OPENAI_KEY_HERE"  # Optional
```

3. Click **"Save"**
4. App will automatically redeploy

#### 4.4 Update Connected App Callback URL

1. Go back to Salesforce Setup → App Manager
2. Find your Connected App → **Manage**
3. Edit **Callback URL** to match your Streamlit Cloud URL:
   ```
   https://your-actual-app-name.streamlit.app/
   ```
4. Save

### Option 2: Local Development/Testing

#### 2.1 Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2.2 Create `.env` File

Create a file named `.env` in your project root:

```bash
# Salesforce OAuth
SF_CLIENT_ID=your_consumer_key
SF_CLIENT_SECRET=your_consumer_secret
SF_REDIRECT_URI=http://localhost:8501/

# AI Keys (add one or both)
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
```

**⚠️ IMPORTANT**: Never commit `.env` to git! It's in .gitignore already.

#### 2.3 Run Locally

```bash
streamlit run main.py
```

App will open at `http://localhost:8501/`

### Option 3: Docker Deployment

#### 3.1 Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### 3.2 Build and Run

```bash
# Build image
docker build -t sf-analyzer .

# Run container (replace with your actual values)
docker run -p 8501:8501 \
  -e SF_CLIENT_ID="your_key" \
  -e SF_CLIENT_SECRET="your_secret" \
  -e SF_REDIRECT_URI="http://localhost:8501/" \
  -e GEMINI_API_KEY="your_gemini_key" \
  -e OPENAI_API_KEY="your_openai_key" \
  sf-analyzer
```

---

## Testing Locally

### 1. Start the App

```bash
streamlit run main.py
```

### 2. Test OAuth Flow

1. App opens at `http://localhost:8501/`
2. You'll see a login screen
3. Click **"Login with Production / Developer Org"** or **"Login with Sandbox"**
4. You'll be redirected to Salesforce login
5. Login with your Salesforce credentials
6. Grant permission to the app
7. You'll be redirected back to the app (now authenticated)

### 3. Test AI Provider Selection

1. In the sidebar, you'll see **"AI Provider"** selection
2. Choose **Gemini** or **OpenAI**
3. The corresponding API key field will appear
4. Enter your API key
5. Upload release notes and run analysis

### 4. Test Logout

1. Click **"Logout"** button in sidebar
2. Your session will be cleared
3. You'll be returned to login screen

---

## Troubleshooting

### OAuth Issues

**Problem**: "redirect_uri_mismatch" error

**Solution**: 
- Ensure Connected App Callback URL exactly matches your deployment URL
- Include trailing slash: `https://app.streamlit.app/` not `https://app.streamlit.app`
- For local: use `http://localhost:8501/` exactly

**Problem**: "invalid_client_id" error

**Solution**:
- Verify SF_CLIENT_ID in secrets matches Consumer Key from Connected App
- Check for extra spaces or quotes in the secret value

**Problem**: User can't see the app after authentication

**Solution**:
- Check Connected App "Permitted Users" setting
- Ensure user has proper profile/permission set assigned

### AI Provider Issues

**Problem**: "Invalid API key" for Gemini

**Solution**:
- Verify key from https://ai.google.dev/
- Check key hasn't expired
- Ensure no extra spaces in .env or secrets

**Problem**: OpenAI rate limit errors

**Solution**:
- Check your OpenAI usage at platform.openai.com
- Verify billing is enabled
- Consider using Gemini (free tier) instead

### General Issues

**Problem**: App crashes on startup

**Solution**:
```bash
# Check logs
streamlit run main.py

# Verify all dependencies installed
pip install -r requirements.txt

# Check for import errors
python3 -c "from salesforce_client import get_authorization_url; print('✅ OAuth helpers loaded')"
python3 -c "from ai_analyzer import AIAnalyzer; print('✅ AI analyzer loaded')"
```

**Problem**: Can't import OpenAI

**Solution**:
```bash
pip install openai>=1.12.0
```

---

## Security Best Practices

### For Production Deployment

1. **Never commit secrets to git**
   - Use platform secret managers (Streamlit Secrets, AWS Secrets Manager, etc.)
   - Keep `.env` in `.gitignore`

2. **Restrict Connected App access**
   - Use "Admin approved users" setting
   - Create a Permission Set for specific users

3. **Use HTTPS only**
   - Streamlit Cloud provides HTTPS automatically
   - For custom hosting, ensure SSL/TLS certificate

4. **Rotate credentials regularly**
   - Change Consumer Secret quarterly
   - Rotate API keys if compromised

5. **Monitor API usage**
   - Check Gemini/OpenAI dashboards for unusual activity
   - Set up billing alerts

---

## Support & Resources

- **Salesforce Connected App Docs**: https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm
- **Streamlit Deployment**: https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app
- **Google Gemini**: https://ai.google.dev/docs
- **OpenAI API**: https://platform.openai.com/docs

---

## Quick Start Checklist

- [ ] Salesforce Connected App created
- [ ] Consumer Key and Secret saved
- [ ] Callback URL configured correctly
- [ ] Code pushed to GitHub (for cloud deployment)
- [ ] Streamlit Cloud app created (or local .env configured)
- [ ] Secrets added (Client ID, Secret, Redirect URI)
- [ ] AI API key(s) added (Gemini and/or OpenAI)
- [ ] Tested OAuth login flow
- [ ] Tested with both AI providers
- [ ] Logout works properly

---

**🎉 You're all set! Users can now securely login and analyze Salesforce releases!**
