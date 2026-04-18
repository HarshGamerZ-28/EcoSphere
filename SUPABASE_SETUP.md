# 🌿 EcoSphere Supabase Setup Guide

This guide will help you set up Supabase as your database for the EcoSphere platform.

## Prerequisites
- Supabase account (free tier available): https://supabase.com
- Your EcoSphere project folder

## Step 1: Create Supabase Project

1. Go to https://supabase.com and sign in
2. Click "New Project"
3. Enter project details:
   - **Name**: `ecosphere-prod` (or your preferred name)
   - **Database Password**: Create a strong password (save it!)
   - **Region**: Choose closest to your users (India: Singapore/Mumbai if available)
   - **Pricing**: Free tier is fine for testing
4. Click "Create new project" and wait for setup (~2-3 mins)

## Step 2: Get Connection String

1. In Supabase dashboard, go to **Settings → Database**
2. Find "Connection string" section
3. Copy the **TRANSACTION** or **SESSION** mode connection string
   - Format: `postgresql://[user]:[password]@[host]:[port]/[database]`
4. **Replace `[user]` with actual postgres user password** (check if needed)
5. Save this for later

## Step 3: Update Backend .env

Edit `ecoloop-backend/.env` and add:

```env
# Supabase PostgreSQL Connection
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres

# Keep other settings
GEMINI_API_KEY=your_gemini_key
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

**Important**: Get your connection string from Supabase dashboard → Settings → Database → Connection string (copy the "URL" field)

## Step 4: Test Connection

Run this from your backend folder:

```bash
python -c "
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
load_dotenv()
db_url = os.getenv('DATABASE_URL')
print(f'Testing connection to: {db_url[:50]}...')
engine = create_engine(db_url, echo=False, pool_pre_ping=True)
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('✅ Connection successful!')
"
```

If you get an error, check:
- DATABASE_URL is correctly formatted
- Password doesn't contain special characters (if it does, URL-encode them: @ = %40, : = %3A, etc.)
- Network access: Supabase → Project Settings → Database → Check "Connection pooler" is enabled

## Step 5: Run Migrations

Once connection is verified, your tables will auto-create on first FastAPI startup.

```bash
cd ecoloop-backend
python main.py
```

Check terminal output for:
```
✅ Database tables initialized
🐘 Using PostgreSQL database
```

## Step 6: Verify Tables in Supabase

1. Go to Supabase dashboard
2. Click **SQL Editor** on the left
3. Click **New Query**
4. Paste:
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' ORDER BY table_name;
```
5. You should see: `users`, `listings`, `quote_requests`, `green_scores`, `chat_messages`, etc.

## Step 7: Update Frontend (Optional)

If you want to track Supabase events:

```javascript
// In ecoloop-frontend/js/api.js, add monitoring:
const DB_SUPABASE = true;
const API_BASE = (window.location.hostname === 'localhost')
  ? 'http://localhost:8000/api'
  : 'https://your-deployed-backend.com/api';
```

## Step 8: Deploy to Production

When deploying to Vercel/Render/Railway:

1. Add environment variable `DATABASE_URL` with your Supabase connection string
2. Ensure the connection pooler is enabled in Supabase
3. Redeploy your backend
4. Test with `curl https://your-backend.com/api/listings`

## Important Notes

### Connection Pooler vs Direct Connection

- **Pooler Mode** (Recommended for Vercel/Railway): Append `:6543` to host, use less resources
  ```
  postgresql://postgres.[ID]:[PASS]@aws-0-[region].pooler.supabase.com:6543/postgres
  ```
- **Direct Connection** (For local): No port change
  ```
  postgresql://postgres.[ID]:[PASS]@aws-0-[region].db.supabase.com:5432/postgres
  ```

### Backups

Supabase automatically backs up your data daily. To restore:
1. Go to **Settings → Database → Backups**
2. Click restore on the desired backup

### Security

- Never commit `.env` files to Git
- Use environment secrets in your deployment platform (Vercel, Railway, etc.)
- Enable RLS (Row Level Security) in Supabase for additional protection

## Troubleshooting

### "Too many connections" error
→ Check connection pooler is enabled, reduce `pool_size` in `database.py`

### "FATAL: password authentication failed"
→ Re-copy connection string from Supabase, ensure special chars are URL-encoded

### Tables not created on startup
→ Check database.py has `Base.metadata.create_all(bind=engine)` and no errors in logs

### Can't connect from deployed app
→ Ensure Supabase network access allows your app's IP, or use connection pooler

## Next Steps

1. ✅ Database is ready!
2. 📧 Configure email (SMTP_USER, SMTP_PASSWORD in .env)
3. 🤖 Set GEMINI_API_KEY for AI features
4. 🚀 Deploy to production

## Support

- Supabase Docs: https://supabase.com/docs
- EcoSphere Issues: Check backend logs with `docker logs` or deployment logs
