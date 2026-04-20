# SSL Certificate Troubleshooting Guide 🔒

## Issue: CERTIFICATE_VERIFY_FAILED Error

If you see errors like this:
```
SSL_ERROR_SSL: error:1000007d:SSL routines:OPENSSL_internal:CERTIFICATE_VERIFY_FAILED: 
self signed certificate in certificate chain
```

This typically occurs in **corporate networks** with SSL inspection/interception.

---

## 🔍 What's Happening?

Your company's network likely uses a **proxy/firewall that intercepts HTTPS traffic**:
1. Your app tries to connect to Salesforce/Google APIs
2. Corporate proxy intercepts the connection
3. Proxy presents its own SSL certificate (signed by your company's CA)
4. Python doesn't recognize the company CA certificate
5. Connection fails with "CERTIFICATE_VERIFY_FAILED"

---

## ✅ Solution 1: Disable SSL Verification (Quick Fix)

**⚠️ Use only in trusted corporate networks**

1. Open your `.env` file
2. Add this line:
```bash
SSL_VERIFY=false
```

3. Restart the Streamlit app

The app will now bypass SSL certificate verification.

---

## ✅ Solution 2: Install Corporate CA Certificate (Recommended)

This is the **proper production solution**:

### Step 1: Get Your Company's CA Certificate
- Ask your IT department for the CA certificate file (usually `.crt` or `.pem`)
- Or export it from your browser:
  - **Chrome/Edge**: Settings → Privacy & Security → Security → Manage Certificates
  - **Firefox**: Settings → Privacy & Security → View Certificates

### Step 2: Install the Certificate

#### macOS:
```bash
# Add to system keychain
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /path/to/company-ca.crt
```

#### Windows:
1. Double-click the `.crt` file
2. Click "Install Certificate"
3. Choose "Local Machine"
4. Place in "Trusted Root Certification Authorities"

#### Linux:
```bash
# Ubuntu/Debian
sudo cp /path/to/company-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# RHEL/CentOS
sudo cp /path/to/company-ca.crt /etc/pki/ca-trust/source/anchors/
sudo update-ca-trust
```

### Step 3: Update Python's Certificate Bundle
```bash
# Install certifi
pip install --upgrade certifi

# Verify Python sees the certificate
python3 -c "import ssl; print(ssl.get_default_verify_paths())"
```

---

## ✅ Solution 3: Set Custom Certificate Bundle

If you can't install system-wide, point to a custom certificate file:

1. Create a combined certificate bundle:
```bash
cat /path/to/company-ca.crt >> custom-bundle.pem
curl https://curl.se/ca/cacert.pem >> custom-bundle.pem
```

2. Set environment variable:
```bash
export REQUESTS_CA_BUNDLE=/path/to/custom-bundle.pem
```

3. Or add to `.env`:
```bash
REQUESTS_CA_BUNDLE=/path/to/custom-bundle.pem
```

---

## 🧪 Testing

After applying a solution, test the connection:

```python
import requests
response = requests.get('https://login.salesforce.com')
print(f"✅ Connected! Status: {response.status_code}")
```

---

## 🆘 Still Having Issues?

### Check Proxy Settings
Your corporate network might also require proxy configuration:

```bash
# Add to .env
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

### Check Firewall
- Ensure ports **443 (HTTPS)** and **8501 (Streamlit)** are allowed
- Ask IT to whitelist: `*.salesforce.com`, `*.google.com`, `*.openai.com`

### Alternative: Use VPN
If you have a corporate VPN, connect before running the app.

---

## 📝 For Production Deployment

**Never disable SSL verification in production!** Always use one of these:
- ✅ Properly installed CA certificates (Solution 2)
- ✅ Custom certificate bundle (Solution 3)
- ❌ Never use `SSL_VERIFY=false` in production

---

## 🔗 Technical Details

The fix modifies these components:
- `salesforce_client.py`: Adds `verify=SSL_VERIFY` to all `requests.post()` calls
- `SalesforceOrgScanner`: Uses custom session with SSL verification control
- Environment variable `SSL_VERIFY` controls behavior (defaults to `true`)

When `SSL_VERIFY=false`:
- All HTTPS requests skip certificate validation
- SSL warnings are suppressed (via `urllib3.disable_warnings()`)
- A warning message is shown: "⚠️ SSL certificate verification disabled"

---

## 📞 Contact IT Support

If none of these work, contact your IT department and ask:
1. "Do we use SSL inspection on our network?"
2. "Can you provide the corporate CA certificate?"
3. "What proxy settings should I use for external API calls?"
4. "Can you whitelist Salesforce and Google Gemini API endpoints?"
