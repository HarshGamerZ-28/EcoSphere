from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# ── Auth ───────────────────────────────────────────
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    company_name: str = Field(..., min_length=2)
    gst_number: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    company_name: str
    gst_number: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    industry: Optional[str]
    is_verified: bool
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# ── Listings ───────────────────────────────────────
class ListingCreate(BaseModel):
    title: str = Field(..., min_length=3)
    category: str
    quantity: str
    price_per_unit: float = Field(..., gt=0)
    unit: str = "kg"
    location: str
    description: Optional[str] = None

class ListingOut(BaseModel):
    id: int
    title: str
    category: str
    quantity: str
    price_per_unit: float
    unit: str
    location: str
    description: Optional[str]
    is_verified: bool
    is_active: bool
    green_pts_value: int
    created_at: datetime
    owner_id: int
    company_name: Optional[str] = None
    class Config:
        from_attributes = True

class ListingUpdate(BaseModel):
    title: Optional[str] = None
    quantity: Optional[str] = None
    price_per_unit: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

# ── Green Score ────────────────────────────────────
class GreenScoreOut(BaseModel):
    id: int
    user_id: int
    total_score: int
    tier: str
    waste_listed_pts: int
    exchange_pts: int
    co2_pts: int
    compliance_pts: int
    rating_pts: int
    zero_waste_pts: int
    updated_at: datetime
    class Config:
        from_attributes = True

class ScoreEventOut(BaseModel):
    id: int
    points: int
    reason: str
    category: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# ── Quotes ─────────────────────────────────────────
class QuoteCreate(BaseModel):
    listing_id: int
    message: Optional[str] = None
    quantity_needed: Optional[str] = None

class QuoteOut(BaseModel):
    id: int
    listing_id: int
    buyer_id: int
    seller_id: int
    message: Optional[str]
    quantity_needed: Optional[str]
    status: str
    buyer_rating: Optional[float]
    seller_rating: Optional[float]
    created_at: datetime
    listing_title: Optional[str] = None
    buyer_company: Optional[str] = None
    seller_company: Optional[str] = None
    class Config:
        from_attributes = True

class QuoteStatusUpdate(BaseModel):
    status: str  # accepted / rejected / completed

class RatingSubmit(BaseModel):
    rating: float = Field(..., ge=1, le=5)
    role: str  # "buyer" or "seller"

# ── AI Matcher ─────────────────────────────────────
class AIMatchRequest(BaseModel):
    waste_name: str
    category: str
    quantity: Optional[str] = None
    description: Optional[str] = None

class AIMatchResult(BaseModel):
    company: str
    type: str
    location: str
    score: int
    reasoning: str
    co2_saved: str
    price_range: str
    tags: List[str]
    compliance: str

class AIMatchResponse(BaseModel):
    matches: List[AIMatchResult]
    used_real_ai: bool
    reasoning_summary: str

class AIDescriptionRequest(BaseModel):
    waste_name: str
    category: str

class AIInsightRequest(BaseModel):
    waste_name: str
    category: str

# ── Leaderboard ────────────────────────────────────
class LeaderboardEntry(BaseModel):
    rank: int
    company_name: str
    location: Optional[str]
    industry: Optional[str]
    score: int
    tier: str
    initials: str
    is_you: bool = False

class PlatformStats(BaseModel):
    total_companies: int
    total_listings: int
    total_exchanges: int
    co2_saved_tonnes: float
    value_generated_cr: float

# ── Chat ────────────────────────────────────────────
class ChatMessageCreate(BaseModel):
    quote_id: int
    receiver_id: int
    message: str

class ChatMessageOut(BaseModel):
    id: int
    quote_id: int
    sender_id: int
    receiver_id: int
    message: str
    is_read: bool
    created_at: datetime
    class Config:
        from_attributes = True

class ChatConversationOut(BaseModel):
    user_id: int
    user_name: str
    last_message: Optional[str]
    unread_count: int
    quote_id: int

# ── Progress Tracking ────────────────────────────────
class ProgressUpdateCreate(BaseModel):
    stage: str
    note: Optional[str] = None

class ProgressUpdateOut(BaseModel):
    id: int
    quote_id: int
    stage: str
    note: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

# ── Quote Status ────────────────────────────────────
class QuoteUpdate(BaseModel):
    status: str  # 'accepted', 'rejected', 'completed'

# ── Payments ───────────────────────────────────────
class PaymentCreate(BaseModel):
    quote_id: int
    amount_inr: float

class PaymentOut(BaseModel):
    id: int
    user_id: int
    quote_id: Optional[int]
    razorpay_order_id: Optional[str]
    razorpay_payment_id: Optional[str]
    amount_paise: int
    currency: str
    status: str
    description: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
