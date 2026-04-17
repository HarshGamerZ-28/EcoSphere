
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from models.database import Base, engine, SessionLocal, User, Listing, GreenScore
from core.auth import hash_password
from core.green_score import get_or_create_score

# ── Create tables ──────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EcoSphere API",
    description="B2B Industrial Waste Exchange Platform — Powered by Gemini AI",
    version="1.0.0",
)

# ── CORS ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ────────────────────────────────────────
from routers import auth, listings, quotes, greenscore, ai as ai_router, payments, admin

app.include_router(auth.router,        prefix="/api")
app.include_router(listings.router,    prefix="/api")
app.include_router(quotes.router,      prefix="/api")
app.include_router(greenscore.router,  prefix="/api")
app.include_router(ai_router.router,   prefix="/api")
app.include_router(payments.router,    prefix="/api")
app.include_router(admin.router,       prefix="/api")


# ── Static Files (Frontend) ───────────────────────
frontend_path = os.path.join(os.path.dirname(__file__), '../ecoloop-frontend')
app.mount("/css", StaticFiles(directory=os.path.join(frontend_path, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_path, "js")), name="js")
app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

# Serve index.html for the SPA
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# Optional: catch-all for SPA routes (e.g., /marketplace, /sell, etc.)
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def spa_catch_all(full_path: str):
    # Only serve index.html for non-API, non-static routes
    if full_path.startswith("api/") or full_path.startswith("css/") or full_path.startswith("js/") or full_path.startswith("assets/"):
        return
    return FileResponse(os.path.join(frontend_path, "index.html"))

# ── Seed data ──────────────────────────────────────
def seed_db():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return  # already seeded

        companies = [
            ("greenmetalinc@ecosphere.in",   "GreenMetal Inc",       "Pune, Maharashtra",     "Metal Recycling"),
            ("chemsynth@ecosphere.in",        "ChemSynth Corp",       "Chennai, Tamil Nadu",   "Chemical Processing"),
            ("fabricfirst@ecosphere.in",      "FabricFirst Pvt Ltd",  "Surat, Gujarat",        "Textile Recycling"),
            ("circuittech@ecosphere.in",      "CircuitTech",          "Bangalore, Karnataka",  "E-Waste Processing"),
            ("techplast@ecosphere.in",        "TechPlast Industries", "Mumbai, Maharashtra",   "Plastic Manufacturing"),
            ("packright@ecosphere.in",        "PackRight Solutions",  "Delhi NCR",             "Packaging"),
            ("metalworks@ecosphere.in",       "MetalWorks Ltd.",      "Pune, Maharashtra",     "Metal Fabrication"),
        ]
        seed_scores = [980, 910, 875, 820, 720, 690, 730]

        users = []
        for (email, name, location, industry), score_pts in zip(companies, seed_scores):
            user = User(
                email=email, hashed_password=hash_password("ecosphere123"),
                company_name=name, location=location, industry=industry,
                is_verified=True,
            )
            db.add(user)
            db.flush()
            gs = GreenScore(user_id=user.id, total_score=score_pts,
                            tier="Gold" if score_pts>=1000 else ("Silver" if score_pts>=500 else "Bronze"),
                            waste_listed_pts=min(200, score_pts//5),
                            exchange_pts=min(300, score_pts//3),
                            co2_pts=min(200, score_pts//6),
                            compliance_pts=min(100, score_pts//10),
                            rating_pts=min(100, score_pts//10),
                            zero_waste_pts=min(100, max(0, score_pts-900)))
            db.add(gs)
            users.append(user)

        db.commit()

        # Seed listings
        demo_listings = [
            (users[4], "HDPE Granules",       "Plastic Scrap",       "500 kg",   45.0,  "Mumbai, Maharashtra",   "Food-grade HDPE granules from manufacturing process. High purity, clean material."),
            (users[6], "Aluminum Chips",      "Metal Waste",         "1,200 kg", 120.0, "Pune, Maharashtra",     "Aluminum machining chips from CNC operations. No coolant contamination."),
            (users[1], "Glycerin (Industrial)","Chemical Byproduct",  "800 L",    35.0,  "Chennai, Tamil Nadu",   "Industrial glycerin byproduct from biodiesel production. 85% purity."),
            (users[2], "Cotton Scraps",        "Textile Waste",       "350 kg",   25.0,  "Surat, Gujarat",        "Cotton fabric offcuts from garment manufacturing. Mixed colors."),
            (users[3], "PCB Boards (Scrap)",   "Electronic Waste",    "200 kg",   180.0, "Bangalore, Karnataka",  "End-of-life PCB boards. CPCB compliant. Precious metal recovery possible."),
            (users[5], "Cardboard Scrap",      "Paper Waste",         "2,000 kg", 12.0,  "Delhi NCR",             "Corrugated cardboard manufacturing waste. Dry, clean, baled."),
        ]
        for owner, title, cat, qty, price, loc, desc in demo_listings:
            l = Listing(title=title, category=cat, quantity=qty, price_per_unit=price,
                        location=loc, description=desc, owner_id=owner.id,
                        is_verified=True, green_pts_value=max(20, int(price*0.8)))
            db.add(l)
        db.commit()
        print("✅ Database seeded with demo data")
    except Exception as e:
        db.rollback()
        print(f"Seed error (non-fatal): {e}")
    finally:
        db.close()

seed_db()

# ── Serve frontend static files ────────────────────
frontend_path = os.path.join(os.path.dirname(__file__), "..", "ecoloop-frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))

# ── Health check ───────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "app": "EcoSphere API v1.0", "docs": "/docs"}

@app.get("/api")
def api_root():
    return {
        "message": "EcoSphere API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth":       "/api/auth/register, /api/auth/login, /api/auth/me",
            "listings":   "/api/listings/",
            "quotes":     "/api/quotes/",
            "greenscore": "/api/greenscore/me, /api/greenscore/leaderboard",
            "ai":         "/api/ai/match, /api/ai/generate-description, /api/ai/insights",
            "payments":   "/api/payments/create-order, /api/payments/verify, /api/payments/my",
            "admin":      "/api/admin/stats, /api/admin/listings/pending, /api/admin/users",
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
