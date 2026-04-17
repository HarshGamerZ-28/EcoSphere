"""
EcoSphere — Razorpay Payment Gateway Router
Handles order creation, payment verification, and webhooks
"""
import os
import hmac
import hashlib
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from models.database import get_db, Payment, QuoteRequest, User, Listing
from models.schemas import PaymentCreate, PaymentOut, PaymentVerify
from core.auth import get_current_user
from core.email_service import send_payment_confirmation
from core.whatsapp_service import wa_payment_confirmed

logger = logging.getLogger(__name__)

RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

router = APIRouter(prefix="/payments", tags=["Payments"])


def get_razorpay_client():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        return None
    try:
        import razorpay
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except ImportError:
        logger.warning("razorpay package not installed. Run: pip install razorpay")
        return None


class OrderRequest(BaseModel):
    quote_id: int
    amount_inr: float          # full amount in INR


class VerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/create-order")
def create_order(
    payload: OrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a Razorpay order for a quote."""
    quote = db.query(QuoteRequest).filter(
        QuoteRequest.id == payload.quote_id,
        QuoteRequest.buyer_id == current_user.id,
        QuoteRequest.status == "accepted",
    ).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found or not accepted")

    amount_paise = int(payload.amount_inr * 100)
    listing_title = quote.listing.title if quote.listing else "Waste Material"

    client = get_razorpay_client()
    if not client:
        # Demo mode: return a mock order so the frontend can still test
        mock_order_id = f"order_demo_{quote.id}_{amount_paise}"
        payment = Payment(
            user_id=current_user.id,
            quote_id=quote.id,
            razorpay_order_id=mock_order_id,
            amount_paise=amount_paise,
            status="created",
            description=f"Payment for {listing_title}",
        )
        db.add(payment)
        db.commit()
        return {
            "order_id": mock_order_id,
            "amount": amount_paise,
            "currency": "INR",
            "key_id": "demo_mode",
            "listing_title": listing_title,
            "demo_mode": True,
        }

    order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"ecosphere_quote_{quote.id}",
        "notes": {
            "quote_id": str(quote.id),
            "buyer": current_user.company_name,
            "listing": listing_title,
        }
    })

    payment = Payment(
        user_id=current_user.id,
        quote_id=quote.id,
        razorpay_order_id=order["id"],
        amount_paise=amount_paise,
        status="created",
        description=f"Payment for {listing_title}",
    )
    db.add(payment)
    db.commit()

    return {
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key_id": RAZORPAY_KEY_ID,
        "listing_title": listing_title,
        "demo_mode": False,
    }


@router.post("/verify")
def verify_payment(
    payload: VerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify Razorpay payment signature and mark as paid."""
    payment = db.query(Payment).filter(
        Payment.razorpay_order_id == payload.razorpay_order_id,
        Payment.user_id == current_user.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    # Verify HMAC signature
    if RAZORPAY_KEY_SECRET:
        sign_data = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
        expected = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            sign_data.encode(),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, payload.razorpay_signature):
            payment.status = "failed"
            db.commit()
            raise HTTPException(status_code=400, detail="Payment signature verification failed")

    payment.razorpay_payment_id = payload.razorpay_payment_id
    payment.razorpay_signature  = payload.razorpay_signature
    payment.status              = "paid"
    db.commit()
    db.refresh(payment)

    amount_inr = payment.amount_paise / 100
    listing_title = payment.description.replace("Payment for ", "") if payment.description else "Waste Material"

    # Fire notifications
    try:
        send_payment_confirmation(
            current_user.email,
            current_user.company_name,
            listing_title,
            amount_inr,
            payload.razorpay_payment_id,
        )
    except Exception as e:
        logger.warning(f"Payment email failed: {e}")

    try:
        if current_user.phone:
            wa_payment_confirmed(current_user.phone, listing_title, amount_inr, payload.razorpay_payment_id)
    except Exception as e:
        logger.warning(f"Payment WhatsApp failed: {e}")

    return {
        "status": "success",
        "payment_id": payload.razorpay_payment_id,
        "amount_inr": amount_inr,
        "message": "Payment verified and confirmed ✅",
    }


@router.get("/my")
def my_payments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all payments made by the current user."""
    payments = db.query(Payment).filter(Payment.user_id == current_user.id)\
                 .order_by(Payment.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "amount_inr": p.amount_paise / 100,
            "status": p.status,
            "description": p.description,
            "payment_id": p.razorpay_payment_id,
            "created_at": p.created_at.isoformat(),
        }
        for p in payments
    ]


@router.get("/razorpay-key")
def get_razorpay_key():
    """Return public Razorpay key for frontend."""
    return {"key_id": RAZORPAY_KEY_ID or "RAZORPAY_NOT_CONFIGURED"}
