# EcoSphere 🌿 — Full Stack
### B2B Industrial Waste Exchange Platform
**By IA (Innovators Arena)**

---

## 🗂 Project Structure

```
ecosphere-project/
├── ecoloop-frontend/          ← Vanilla HTML/CSS/JS frontend
│   ├── index.html             ← Single-page app (6 pages)
│   ├── css/style.css          ← Design system (1000+ lines)
│   ├── js/app.js              ← App logic + localStorage fallback
│   ├── js/api.js              ← Backend API client
│   └── assets/logo.png        ← App Logo
│
├── ecoloop-backend/           ← FastAPI Python backend
│   ├── main.py                ← App entry point + seed data
│   ├── requirements.txt
│   ├── routers/
│   │   ├── auth.py            ← Register, login, profile
│   │   ├── listings.py        ← CRUD waste listings
│   │   ├── quotes.py          ← Quote requests + ratings
│   │   ├── greenscore.py      ← Score dashboard + leaderboard
│   │   └── ai.py              ← Gemini AI endpoints
│   ├── models/
│   │   ├── database.py        ← SQLAlchemy models + SQLite
│   │   └── schemas.py         ← Pydantic request/response schemas
│   └── core/
│       ├── auth.py            ← JWT + bcrypt
│       ├── green_score.py     ← Point award logic + tier calc
│       └── gemini.py          ← Gemini API service + fallbacks
│
└── start.sh                   ← One-command startup
```

---

## 🚀 Quick Start

### Option 1: Backend + Frontend (Full Stack)

```bash
# Step 1: Start backend
cd ecoloop-backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Step 2: Open frontend (new terminal)
cd ecoloop-frontend
python3 -m http.server 3000
# Open: http://localhost:3000
```

### Option 2: Frontend Only (no backend)
```bash
cd ecoloop-frontend
# Just open index.html in browser — works with localStorage
```

### Option 3: One command
```bash
bash start.sh
```

---

## 🔑 Demo Credentials

| Company | Email | Password |
|---|---|---|
| TechPlast Industries | techplast@ecosphere.in | ecosphere123 |
| GreenMetal Inc | greenmetalinc@ecosphere.in | ecosphere123 |
| ChemSynth Corp | chemsynth@ecosphere.in | ecosphere123 |
| CircuitTech | circuittech@ecosphere.in | ecosphere123 |

---

## 🤖 Gemini AI Setup

1. Get free API key: [aistudio.google.com](https://aistudio.google.com)
2. In app navbar → **"🔑 Add API Key"** → paste key → Save
3. AI Matcher, description generation, and insights now use real Gemini 2.0 Flash

**Without API key:** App works in demo mode with curated fallback data.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/auth/register | Create company account |
| POST | /api/auth/login | Login, get JWT token |
| GET  | /api/auth/me | Get current user |
| GET  | /api/listings/ | Browse all listings |
| POST | /api/listings/ | Create waste listing |
| PUT  | /api/listings/{id} | Update listing |
| DELETE | /api/listings/{id} | Deactivate listing |
| POST | /api/quotes/ | Send quote request |
| GET  | /api/quotes/sent | My sent quotes |
| GET  | /api/quotes/received | Quotes I received |
| PUT  | /api/quotes/{id}/status | Accept/reject/complete |
| POST | /api/quotes/{id}/rate | Rate exchange (1–5★) |
| GET  | /api/greenscore/me | My score + history |
| GET  | /api/greenscore/leaderboard | Company rankings |
| GET  | /api/greenscore/stats | Platform-wide stats |
| POST | /api/ai/match | AI waste matching |
| POST | /api/ai/generate-description | AI listing description |
| POST | /api/ai/insights | AI market insights |

API Docs (Swagger): http://localhost:8000/docs

---

## 🌿 GreenScore™ Point System

| Event | Points | Cap |
|---|---|---|
| List waste on marketplace | +45 | 200 max |
| Exchange completed | +120 | Unlimited |
| CO₂ avoided (per 100kg) | +10 | 200 max |
| Compliance doc uploaded | +40 | 100 max |
| Rating received (5★) | +20 | 100 max |
| Profile completed | +30 | 100 max |
| AI Matcher used | +25 | Unlimited |

**Tiers:** Bronze (0–499) → Silver (500–999) → Gold (1000+)

---

## 🌐 Free Deployment

### Backend (Render.com — free tier)
```bash
# Create render.yaml in ecoloop-backend/
services:
  - type: web
    name: ecoloop-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend (Netlify — drag & drop)
- Go to netlify.com/drop
- Drag the `ecoloop-frontend/` folder
- Done! Update `API_BASE` in `js/api.js` to your Render URL

### Frontend (GitHub Pages)
```bash
git init && git add . && git commit -m "EcoSphere v1"
git remote add origin https://github.com/HarshGamerZ/ecosphere
git push -u origin main
# Settings → Pages → Deploy from main branch
```

---

## 🔧 Next Steps (Production)

- [ ] Add PostgreSQL (replace SQLite) for production
- [ ] Email notifications for quote requests (SMTP/SendGrid)
- [ ] File upload for MSDS/compliance documents (AWS S3/Cloudinary)
- [ ] WhatsApp Business API for quote alerts
- [ ] Admin dashboard for listing verification
- [ ] Payment gateway integration (Razorpay)
- [ ] Mobile app (React Native / Flutter)

---

## 👨‍💻 Developer

**Harsh** — B.Tech CSE, GEC Ajmer | GitHub: [@HarshGamerZ](https://github.com/HarshGamerZ)  
**Team:** IA (Innovators Arena)

---

*Built with 💚 for India's circular economy*
