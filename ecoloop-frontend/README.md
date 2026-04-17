# EcoSphere 🌿
### B2B Industrial Waste Exchange Platform
**By IA (Innovators Arena)**

---

## 🚀 Overview

EcoSphere is a complete B2B web platform that connects industrial companies so that the **waste of one company becomes the raw material of another** — powered by **Google Gemini AI**.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Marketplace** | Browse 500+ industrial waste listings with category filters |
| **AI Matcher** | Gemini AI finds the best buyers for your waste in seconds |
| **Sell Waste** | List your waste with AI-generated descriptions |
| **Green Score** | Earn points for every sustainable action — Bronze → Silver → Gold |
| **Leaderboard** | Company rankings with tier benefits |
| **Contact** | Business inquiry form |

---

## 🤖 Gemini AI Integration

EcoSphere uses **Google Gemini 2.0 Flash** for:

1. **AI Waste Matching** — Analyzes waste material and finds the best verified buyers
2. **Description Generation** — Auto-writes professional listing descriptions
3. **Waste Insights** — Market pricing, recycling methods, CO₂ impact

### How to get your Gemini API Key:
1. Go to [https://aistudio.google.com](https://aistudio.google.com)
2. Sign in with Google account
3. Click "Get API Key" → "Create API Key"
4. Copy the key (starts with `AIzaSy...`)
5. In EcoSphere → click **"🔑 Add API Key"** in navbar → paste key → Save

> **Free tier**: 15 requests/minute, 1 million tokens/day — enough for demo usage.

---

## 📁 Project Structure

```
ecosphere/
├── index.html          # Main SPA (all pages)
├── css/
│   └── style.css       # Complete design system
├── js/
│   └── app.js          # App logic + Gemini API integration
├── assets/
│   └── logo.png        # App logo
└── README.md           # This file
```

---

## 🏃 Running the App

### Option 1: Direct (simplest)
Just open `index.html` in your browser — it works without a server for most features.

### Option 2: Local Server (recommended for full functionality)
```bash
# Python 3
cd ecosphere
python -m http.server 3000
# Open: http://localhost:3000

# Node.js (npx)
npx serve .
# Open: http://localhost:3000

# VS Code: Install "Live Server" extension → Right-click index.html → "Open with Live Server"
```

---

## 🌿 GreenScore™ System

Companies earn points for:

| Action | Points |
|---|---|
| List waste on platform | +45 pts |
| Complete an exchange | +120 pts |
| Upload compliance document | +40 pts |
| Receive 5★ rating | +20 pts |
| Use AI Matcher | +25 pts |
| CO₂ emissions avoided | +1 pt per 10kg |

**Tiers:**
- 🌱 **Bronze** (0–499): Basic listing + analytics
- ⚡ **Silver** (500–999): Priority listing + AI alerts + GST reports
- 🏆 **Gold** (1000+): Featured badge + Carbon certificate + Govt incentives

---

## 🛠 Tech Stack

- **Frontend**: Vanilla HTML5 + CSS3 + JavaScript (ES6+)
- **AI**: Google Gemini 2.0 Flash API
- **Fonts**: Plus Jakarta Sans (headings) + DM Sans (body)
- **Storage**: localStorage for listings, scores, API key
- **No build tools required** — pure vanilla stack

---

## 📦 Deployment

### Free Options:
1. **GitHub Pages** — Push repo → Settings → Pages → Deploy from main
2. **Netlify** — Drag & drop the `ecosphere/` folder at netlify.com/drop
3. **Vercel** — `npx vercel` in project directory
4. **Render** — Connect GitHub repo, static site

---

## 🔧 Backend Integration (Next Steps)

To make this production-ready, add:

```
backend/
├── FastAPI or Node.js/Express
├── PostgreSQL (listings, companies, scores)
├── JWT authentication
├── File upload (MSDS, compliance docs)
├── Email notifications (quote requests)
└── Webhook for real-time updates
```

---

## 👨‍💻 Developer

**Harsh** — B.Tech CSE, Government Engineering College Ajmer  
GitHub: [@HarshGamerZ](https://github.com/HarshGamerZ)  
Team: IA (Innovators Arena)

---

## 📄 License

MIT License — Free to use and modify for educational and commercial purposes.

---

*Built with 💚 for India's circular economy*
