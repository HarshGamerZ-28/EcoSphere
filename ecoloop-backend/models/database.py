from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

# ── Database URL ────────────────────────────────────
# Uses PostgreSQL if DATABASE_URL is set in .env, otherwise falls back to SQLite
_db_url = os.getenv("DATABASE_URL", "")

if _db_url and _db_url.startswith("postgresql"):
    # PostgreSQL — production
    SQLALCHEMY_DATABASE_URL = _db_url
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
    print(f"🐘 Using PostgreSQL database")
else:
    # SQLite — development fallback
    SQLALCHEMY_DATABASE_URL = "sqlite:///./ecoloop.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    print(f"🗃️  Using SQLite database (set DATABASE_URL in .env for PostgreSQL)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Enums ──────────────────────────────────────────
class TierEnum(str, enum.Enum):
    bronze = "Bronze"
    silver = "Silver"
    gold   = "Gold"

class WasteCategory(str, enum.Enum):
    plastic    = "Plastic Scrap"
    metal      = "Metal Waste"
    chemical   = "Chemical Byproduct"
    textile    = "Textile Waste"
    electronic = "Electronic Waste"
    paper      = "Paper Waste"
    organic    = "Organic Waste"
    rubber     = "Rubber / Polymer"

class QuoteStatus(str, enum.Enum):
    pending   = "pending"
    accepted  = "accepted"
    rejected  = "rejected"
    completed = "completed"

class PaymentStatus(str, enum.Enum):
    pending   = "pending"
    created   = "created"
    paid      = "paid"
    failed    = "failed"
    refunded  = "refunded"

# ── Models ─────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id               = Column(Integer, primary_key=True, index=True)
    email            = Column(String, unique=True, index=True, nullable=False)
    hashed_password  = Column(String, nullable=False)
    company_name     = Column(String, nullable=False)
    gst_number       = Column(String, nullable=True)
    phone            = Column(String, nullable=True)
    location         = Column(String, nullable=True)
    industry         = Column(String, nullable=True)
    is_verified      = Column(Boolean, default=False)
    is_active        = Column(Boolean, default=True)
    is_admin         = Column(Boolean, default=False)  # ← Admin dashboard access
    created_at       = Column(DateTime, default=datetime.utcnow)

    listings         = relationship("Listing", back_populates="owner")
    green_score      = relationship("GreenScore", back_populates="user", uselist=False)
    score_events     = relationship("ScoreEvent", back_populates="user")
    sent_quotes      = relationship("QuoteRequest", foreign_keys="QuoteRequest.buyer_id", back_populates="buyer")
    received_quotes  = relationship("QuoteRequest", foreign_keys="QuoteRequest.seller_id", back_populates="seller")
    payments         = relationship("Payment", back_populates="user")

class Listing(Base):
    __tablename__ = "listings"
    id               = Column(Integer, primary_key=True, index=True)
    title            = Column(String, nullable=False)
    category         = Column(String, nullable=False)
    quantity         = Column(String, nullable=False)
    price_per_unit   = Column(Float, nullable=False)
    unit             = Column(String, default="kg")
    location         = Column(String, nullable=False)
    description      = Column(Text, nullable=True)
    is_verified      = Column(Boolean, default=False)
    is_active        = Column(Boolean, default=True)
    verification_note = Column(Text, nullable=True)  # ← Admin notes
    green_pts_value  = Column(Integer, default=20)
    created_at       = Column(DateTime, default=datetime.utcnow)
    owner_id         = Column(Integer, ForeignKey("users.id"))

    owner            = relationship("User", back_populates="listings")
    quote_requests   = relationship("QuoteRequest", back_populates="listing")

class GreenScore(Base):
    __tablename__ = "green_scores"
    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), unique=True)
    total_score         = Column(Integer, default=0)
    tier                = Column(String, default="Bronze")
    waste_listed_pts    = Column(Integer, default=0)
    exchange_pts        = Column(Integer, default=0)
    co2_pts             = Column(Integer, default=0)
    compliance_pts      = Column(Integer, default=0)
    rating_pts          = Column(Integer, default=0)
    zero_waste_pts      = Column(Integer, default=0)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user                = relationship("User", back_populates="green_score")

class ScoreEvent(Base):
    __tablename__ = "score_events"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    points     = Column(Integer, nullable=False)
    reason     = Column(String, nullable=False)
    category   = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user       = relationship("User", back_populates="score_events")

class QuoteRequest(Base):
    __tablename__ = "quote_requests"
    id               = Column(Integer, primary_key=True, index=True)
    listing_id       = Column(Integer, ForeignKey("listings.id"))
    buyer_id         = Column(Integer, ForeignKey("users.id"))
    seller_id        = Column(Integer, ForeignKey("users.id"))
    message          = Column(Text, nullable=True)
    quantity_needed  = Column(String, nullable=True)
    status           = Column(String, default="pending")
    buyer_rating     = Column(Float, nullable=True)
    seller_rating    = Column(Float, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listing          = relationship("Listing", back_populates="quote_requests")
    buyer            = relationship("User", foreign_keys=[buyer_id], back_populates="sent_quotes")
    seller           = relationship("User", foreign_keys=[seller_id], back_populates="received_quotes")
    payment          = relationship("Payment", back_populates="quote", uselist=False)

class AIMatchLog(Base):
    __tablename__ = "ai_match_logs"
    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=True)
    waste_name    = Column(String)
    waste_category = Column(String)
    quantity      = Column(String, nullable=True)
    matches_json  = Column(Text)   # JSON string of results
    used_real_ai  = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    """Razorpay payment records"""
    __tablename__ = "payments"
    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"))
    quote_id            = Column(Integer, ForeignKey("quote_requests.id"), nullable=True)
    razorpay_order_id   = Column(String, unique=True, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    razorpay_signature  = Column(String, nullable=True)
    amount_paise        = Column(Integer, nullable=False)   # in paise (₹1 = 100 paise)
    currency            = Column(String, default="INR")
    status              = Column(String, default="pending")
    description         = Column(String, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user                = relationship("User", back_populates="payments")
    quote               = relationship("QuoteRequest", back_populates="payment")
