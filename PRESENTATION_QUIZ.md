# Salesforce Release Impact Analyzer - Audience Quiz 🎯

## Easy Questions (2)

### Question 1: Authentication Method
**What authentication method does the Salesforce Release Impact Analyzer use for secure connections?**

A) Username and Password  
B) API Keys only  
C) OAuth 2.0 with PKCE  
D) Session tokens  

**Correct Answer:** C) OAuth 2.0 with PKCE  
**Explanation:** The tool uses OAuth 2.0 Web Server Flow with PKCE (Proof Key for Code Exchange) for enhanced security, eliminating the need to store user credentials.

---

### Question 2: AI Provider Support
**Which AI providers can you use for release notes analysis in this tool?**

A) Only Google Gemini  
B) Only OpenAI ChatGPT  
C) Both Gemini and OpenAI (user selectable)  
D) Only custom AI models  

**Correct Answer:** C) Both Gemini and OpenAI (user selectable)  
**Explanation:** The tool supports both Google Gemini and OpenAI with a UI toggle, allowing users to choose their preferred AI provider and enter the corresponding API key.

---

## Medium Questions (2)

### Question 3: PKCE Security
**What does PKCE stand for, and why is it used in OAuth authentication?**

A) Private Key Code Exchange - encrypts the authorization code  
B) Proof Key for Code Exchange - prevents authorization code interception attacks  
C) Public Key Certificate Exchange - validates server identity  
D) Protected Key Credential Exchange - stores credentials securely  

**Correct Answer:** B) Proof Key for Code Exchange - prevents authorization code interception attacks  
**Explanation:** PKCE is an OAuth 2.0 extension (RFC 7636) that prevents authorization code interception by requiring a cryptographically random code_verifier that matches the code_challenge sent during authorization.

---

### Question 4: Analysis Capabilities
**Which of the following analyses can the tool perform? (Select the most complete answer)**

A) Only release notes parsing  
B) Release impact analysis and field usage tracking  
C) Release impact analysis, field usage tracking, and org health monitoring  
D) Only Salesforce metadata extraction  

**Correct Answer:** C) Release impact analysis, field usage tracking, and org health monitoring  
**Explanation:** The tool provides three main features: AI-powered release notes analysis to identify impacted components, field usage analysis across all org components, and comprehensive org health monitoring.

---

## Hard Question (1)

### Question 5: Technical Implementation Challenge
**How does the tool solve the PKCE verifier persistence problem when Streamlit reruns the script during OAuth callback redirects?**

A) Stores verifiers in browser localStorage  
B) Uses session cookies to maintain state  
C) Implements file-based storage (.pkce_storage.json) with session ID tracking via OAuth state parameter  
D) Sends verifiers as URL query parameters  

**Correct Answer:** C) Implements file-based storage (.pkce_storage.json) with session ID tracking via OAuth state parameter  
**Explanation:** Streamlit's session state doesn't persist across external redirects. The solution uses file-based storage where PKCE verifiers are saved to a JSON file keyed by a unique session ID. This session ID is passed through the OAuth flow via the state parameter (format: "sessionID:org_type"), allowing the callback handler to retrieve the correct verifier after Salesforce redirects back. Old verifiers are automatically cleaned up after 10 minutes.

---

## Bonus Discussion Questions 💭

### Question 6: Real-World Application
**In your organization, what would be the biggest benefit of using this tool before a Salesforce release?**
- Proactive impact assessment
- Reduced post-release incidents
- Better stakeholder communication
- Time savings in manual reviews
- All of the above

### Question 7: Deployment Strategy
**For production deployment, which hosting option would be most suitable for your team?**
- Local deployment (each analyst runs on their machine)
- Streamlit Community Cloud (free, public)
- Private cloud deployment (AWS/Azure/GCP)
- Internal server with VPN access

---

## Answer Sheet (For Presenter) 📝

| Question | Answer | Difficulty |
|----------|--------|------------|
| Q1 | C | Easy |
| Q2 | C | Easy |
| Q3 | B | Medium |
| Q4 | C | Medium |
| Q5 | C | Hard |

**Scoring Guide:**
- 5/5 correct: OAuth & AI Integration Expert 🌟
- 4/5 correct: Release Analysis Professional ⭐
- 3/5 correct: Salesforce Enthusiast 👍
- 2/5 correct: Getting Started 📚
- 0-1/5 correct: Great learning opportunity! 🎓
