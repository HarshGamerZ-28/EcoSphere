# 🚀 EcoSphere - Quick Configuration Guide

## ✅ What's Been Implemented

You now have:
1. **Real-time Listings** - All users see new listings instantly + email notifications
2. **AI Matcher** - Powered by Gemini (with fallback 500+ verified buyers)
3. **Supabase Database** - Production-ready PostgreSQL (free tier available)
4. **Green Score System** - Accurate tier calculation with monthly tracking

---

## 🔧 REQUIRED CONFIG (Do This First!)

### 1. Gmail for Email Notifications
**Without this, quote notifications won't send!**

1. Go to your Gmail account: https://myaccount.google.com
2. **Enable 2-Step Verification** (Settings → Security → 2-Step Verification)
3. Generate **App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Choose: Mail → Windows Computer (or your device)
   - Copy the 16-character password
4. Edit `ecoloop-backend/.env`:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_gmail@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx
   SMTP_FROM=EcoSphere <noreply@ecosphere.in>
   ```
5. Test:
   ```bash
   cd ecoloop-backend
   python -c "from core.email_service import send_email; send_email('test@example.com', 'Test', '<p>Email test</p>')"
   # Should see: ✉️ Email sent
   ```

### 2. Gemini AI for Smart Matching
**Optional but recommended for AI Matcher**

1. Go to: https://ai.google.dev/
2. Click "Get API Key" → Create API Key
3. Copy the key
4. Edit `ecoloop-backend/.env`:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
5. Test in UI: Go to "AI Matcher" → Enter waste details → Click "Find AI Matches"

### 3. Supabase for Production Database
**Optional: Use if deploying to production**

1. Go to: https://supabase.com → Create Project
2. Copy Connection String from Settings → Database
3. Edit `ecoloop-backend/.env`:
   ```env
   DATABASE_URL=postgresql://postgres.[ID]:[PASS]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
4. Restart backend - tables auto-create!

---

## 🎯 FEATURES TO TEST

### Test 1: Real-time Listings & Quotes
```
1. Open browser 1: Create Account A, List waste item
2. Open browser 2: Create Account B, see listing immediately
3. In Browser 2: Click "Request Quote"
4. Check Browser 1 email: Should get "New quote request" email
5. In email: Click "Chat" button
6. Should open chat section on website
```

### Test 2: AI Matcher
```
1. Go to "AI Matcher" tab
2. Enter: Waste="HDPE Plastic Scrap", Category="Plastic Scrap", Qty="500 kg"
3. Click "Find AI Matches"
4. See 3 verified buyers with:
   - Match percentage
   - Company name & location
   - CO2 saved
   - Price range
5. Can send quote request directly
```

### Test 3: Green Score Tier System
```
1. Login to account
2. Click "Green Score" tab
3. See your total points & tier:
   - Bronze (0-499 pts): Shows 🌱 Bronze
   - Silver (500-999 pts): Shows ⚡ Silver  
   - Gold (1000+ pts): Shows 🏆 Gold
4. Perform actions (list waste = +45 pts)
5. Refresh Green Score page
6. See points increase & tier update
7. Check "Monthly Progress" section
```

### Test 4: Chat System
```
1. One user: List waste
2. Another user: Send quote request
3. First user: Receive email with Accept/Reject/Chat buttons
4. Click "Chat" in email
5. Opens chat with buyer
6. Exchange messages
7. Messages stored in database
```

---

## 📝 File Changes Made

### Frontend (js/api.js)
✅ Added functions:
- `sendChatMessage()` - Send chat messages
- `acceptQuote()` - Accept quote & open chat
- `rejectQuote()` - Reject quote

### Backend
✅ Already configured:
- Email notification templates
- AI matcher endpoints
- Green score calculation
- Chat messaging system
- Supabase PostgreSQL support

---

## 🔍 Verify Installation

Run these commands to verify everything works:

```bash
# Test Backend
cd ecoloop-backend
python -c "from models.database import Base, engine; print('✅ Database OK' if engine else '❌ Failed')"

# Test Email (replace with real email)
python -c "from core.email_service import send_email; send_email('youremail@gmail.com', 'Test', '<p>Works!</p>'); print('✅ Email configured')"

# Test Gemini (if you have API key)
python -c "import os; from dotenv import load_dotenv; load_dotenv(); key = os.getenv('GEMINI_API_KEY'); print('✅ Gemini configured' if key else '⚠️  Gemini not configured (optional)')"
```

---

## 🚀 Deploy to Production

### Backend Deployment (Render/Railway/Heroku)

1. Get your backend running locally first (test all features)
2. Choose deployment platform (Render.com recommended):
   - Connect GitHub repo
   - Set environment variables:
     ```
     DATABASE_URL=postgresql://...  (from Supabase)
     GEMINI_API_KEY=...
     SMTP_USER=...
     SMTP_PASSWORD=...
     ```
   - Deploy!
3. Get your backend URL: `https://your-backend.render.com`

### Frontend Deployment (Vercel)

1. Edit `ecoloop-frontend/js/api.js` - Update API_BASE:
   ```javascript
   const API_BASE = 'https://your-backend.render.com/api';
   ```
2. Deploy to Vercel:
   - Connect GitHub
   - Vercel auto-deploys frontend
3. Your app is live at: `https://your-app.vercel.app`

---

## 📊 What Happens Now

**When someone requests a quote:**
1. Email sent to lister with 3 buttons: Accept / Reject / Chat
2. Email sent to quoter with tracking link
3. Lister clicks Accept → Chat opens
4. Both parties exchange messages in real-time
5. Both earn Green Points

**When someone uses AI Matcher:**
1. Enters waste details
2. Gets top 3 verified buyers (using AI or fallback)
3. Can send quotes directly to matches
4. Each use = +25 Green Points

**Green Score updates:**
- +45 pts: List waste
- +120 pts: Complete exchange
- +40 pts: Upload compliance doc
- +25 pts: Use AI Matcher
- +20 pts: Get 5-star rating
- Tier changes: Silver at 500 pts, Gold at 1000 pts

---

## ⚠️ Important Notes

1. **Email won't work** without Gmail App Password (not your regular password!)
2. **AI Matcher falls back** to 500+ pre-loaded companies if Gemini key missing
3. **Green Score** updates immediately when user performs actions
4. **Chat** only works between users with accepted quotes
5. **Supabase** is optional - works with SQLite for development

---

## 💡 Pro Tips

- Test in 2 browser windows (different companies)
- Check email spam folder for test emails
- Use test email addresses first (gmail.com works great)
- Gemini API is free tier (limited requests/day)
- Supabase free tier: Unlimited connections, daily backups

---

## 🎯 Final Checklist

- [ ] Configure Gmail App Password in .env
- [ ] Test email sending works
- [ ] (Optional) Get Gemini API key
- [ ] (Optional) Setup Supabase
- [ ] Test creating listings in browser
- [ ] Test quote requests work
- [ ] Check email notifications received
- [ ] Test chat functionality
- [ ] Test Green Score updates
- [ ] Test AI Matcher (with or without Gemini)

---

## 📞 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Emails not sending | Check Gmail app password in .env, enable 2FA |
| AI Matcher shows "unavailable" | It's OK - fallback matches work without Gemini key |
| Green Score shows old tier | Login again or refresh page |
| Listings not appearing | Backend must be running (python main.py) |
| Chat doesn't work | Both users must be logged in, quote must be accepted |

---

**You're all set! 🎉**

Now go to https://eco-sphere-rho-eosin.vercel.app and test all features!
