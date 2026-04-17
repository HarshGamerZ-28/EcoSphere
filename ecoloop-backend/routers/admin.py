"""
EcoSphere — Admin Dashboard Router
Protected routes for listing verification, user management, and analytics
Access requires is_admin=True on the User model.
Bootstrap: POST /api/admin/bootstrap (uses ADMIN_SECRET_KEY from .env)
"""
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from models.database import get_db, User, Listing, QuoteRequest, Payment, GreenScore
from core.auth import get_current_user
from core.email_service import send_listing_verified
from core.whatsapp_service import wa_listing_verified

logger = logging.getLogger(__name__)

ADMIN_SECRET = os.getenv("ADMIN_SECRET_KEY", "ecosphere-admin-secret-change-me")

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Admin Guard ────────────────────────────────────
def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── Bootstrap: promote first admin ─────────────────
class BootstrapRequest(BaseModel):
    secret: str
    email: str

@router.post("/bootstrap", summary="One-time admin setup")
def bootstrap_admin(payload: BootstrapRequest, db: Session = Depends(get_db)):
    """
    Promote a user to admin using the ADMIN_SECRET_KEY from .env.
    Run once to set up your first admin account.
    """
    if payload.secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found — register first")
    user.is_admin = True
    db.commit()
    return {"message": f"✅ {user.company_name} ({user.email}) is now an admin"}


# ── Dashboard Stats ────────────────────────────────
@router.get("/stats", summary="Platform overview stats")
def admin_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    return {
        "total_users":           db.query(User).count(),
        "verified_users":        db.query(User).filter(User.is_verified == True).count(),
        "new_users_this_week":   db.query(User).filter(User.created_at >= week_ago).count(),
        "total_listings":        db.query(Listing).count(),
        "pending_verification":  db.query(Listing).filter(Listing.is_verified == False, Listing.is_active == True).count(),
        "verified_listings":     db.query(Listing).filter(Listing.is_verified == True).count(),
        "total_quotes":          db.query(QuoteRequest).count(),
        "pending_quotes":        db.query(QuoteRequest).filter(QuoteRequest.status == "pending").count(),
        "completed_exchanges":   db.query(QuoteRequest).filter(QuoteRequest.status == "completed").count(),
        "total_payments":        db.query(Payment).count(),
        "paid_payments":         db.query(Payment).filter(Payment.status == "paid").count(),
        "revenue_paise":         sum(p.amount_paise for p in db.query(Payment).filter(Payment.status == "paid").all()),
    }


# ── Listing Verification Queue ─────────────────────
@router.get("/listings/pending", summary="Listings pending verification")
def pending_listings(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    listings = db.query(Listing).filter(
        Listing.is_verified == False,
        Listing.is_active == True
    ).order_by(Listing.created_at.asc()).all()
    return [
        {
            "id": l.id,
            "title": l.title,
            "category": l.category,
            "quantity": l.quantity,
            "price_per_unit": l.price_per_unit,
            "location": l.location,
            "description": l.description,
            "owner_id": l.owner_id,
            "owner_company": l.owner.company_name if l.owner else None,
            "owner_email": l.owner.email if l.owner else None,
            "owner_phone": l.owner.phone if l.owner else None,
            "created_at": l.created_at.isoformat(),
        }
        for l in listings
    ]


class VerifyListingRequest(BaseModel):
    note: Optional[str] = None

@router.post("/listings/{listing_id}/verify", summary="Verify a listing")
def verify_listing(
    listing_id: int,
    payload: VerifyListingRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing.is_verified = True
    listing.verification_note = payload.note
    db.commit()
    db.refresh(listing)

    # Notify seller
    if listing.owner:
        try:
            send_listing_verified(
                listing.owner.email,
                listing.owner.company_name,
                listing.title,
                payload.note,
            )
        except Exception as e:
            logger.warning(f"Verify email failed: {e}")

        try:
            if listing.owner.phone:
                wa_listing_verified(listing.owner.phone, listing.owner.company_name, listing.title)
        except Exception as e:
            logger.warning(f"Verify WhatsApp failed: {e}")

    return {"message": f"✅ Listing '{listing.title}' verified and seller notified."}


@router.post("/listings/{listing_id}/reject", summary="Reject/remove a listing")
def reject_listing(
    listing_id: int,
    payload: VerifyListingRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.is_active = False
    listing.verification_note = payload.note or "Rejected by admin"
    db.commit()
    return {"message": f"❌ Listing '{listing.title}' rejected and deactivated."}


# ── All Listings ───────────────────────────────────
@router.get("/listings/all", summary="All listings with status")
def all_listings(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    listings = db.query(Listing).order_by(Listing.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": l.id,
            "title": l.title,
            "category": l.category,
            "is_verified": l.is_verified,
            "is_active": l.is_active,
            "owner_company": l.owner.company_name if l.owner else None,
            "verification_note": l.verification_note,
            "created_at": l.created_at.isoformat(),
        }
        for l in listings
    ]


# ── User Management ────────────────────────────────
@router.get("/users", summary="All registered users")
def all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "company_name": u.company_name,
            "phone": u.phone,
            "location": u.location,
            "industry": u.industry,
            "is_verified": u.is_verified,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "green_score": u.green_score.total_score if u.green_score else 0,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.post("/users/{user_id}/verify", summary="Verify a company")
def verify_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    db.commit()
    return {"message": f"✅ {user.company_name} is now verified."}


@router.post("/users/{user_id}/deactivate", summary="Deactivate a user")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot deactivate an admin")
    user.is_active = False
    db.commit()
    return {"message": f"❌ {user.company_name} has been deactivated."}


# ── Quotes Overview ────────────────────────────────
@router.get("/quotes", summary="All quote requests")
def all_quotes(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    q = db.query(QuoteRequest)
    if status:
        q = q.filter(QuoteRequest.status == status)
    quotes = q.order_by(QuoteRequest.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": qr.id,
            "listing_title": qr.listing.title if qr.listing else None,
            "buyer": qr.buyer.company_name if qr.buyer else None,
            "seller": qr.seller.company_name if qr.seller else None,
            "status": qr.status,
            "created_at": qr.created_at.isoformat(),
        }
        for qr in quotes
    ]


# ── Payments Overview ──────────────────────────────
@router.get("/payments", summary="All payment records")
def all_payments(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    payments = db.query(Payment).order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": p.id,
            "user": p.user.company_name if p.user else None,
            "amount_inr": p.amount_paise / 100,
            "status": p.status,
            "razorpay_payment_id": p.razorpay_payment_id,
            "description": p.description,
            "created_at": p.created_at.isoformat(),
        }
        for p in payments
    ]
