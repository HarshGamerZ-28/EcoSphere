from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from models.database import get_db, QuoteRequest, Listing, User
from models.schemas import QuoteCreate, QuoteOut, QuoteStatusUpdate, RatingSubmit
from core.auth import get_current_user
from core.green_score import award_points
from core.email_service import (
    send_quote_received, send_quote_confirmation, send_quote_status_update
)
from core.whatsapp_service import (
    wa_new_quote_alert, wa_quote_accepted, wa_quote_rejected, wa_exchange_completed
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quotes", tags=["Quotes"])

def enrich_quote(q: QuoteRequest) -> QuoteOut:
    out = QuoteOut.model_validate(q)
    if q.listing:
        out.listing_title = q.listing.title
    if q.buyer:
        out.buyer_company = q.buyer.company_name
    if q.seller:
        out.seller_company = q.seller.company_name
    return out

@router.post("/", response_model=QuoteOut, status_code=201)
def send_quote(
    payload: QuoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    listing = db.query(Listing).filter(Listing.id == payload.listing_id, Listing.is_active == True).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot request quote on your own listing")
    existing = db.query(QuoteRequest).filter(
        QuoteRequest.listing_id == payload.listing_id,
        QuoteRequest.buyer_id == current_user.id,
        QuoteRequest.status == "pending"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Quote request already pending")
    quote = QuoteRequest(
        listing_id=payload.listing_id,
        buyer_id=current_user.id,
        seller_id=listing.owner_id,
        message=payload.message,
        quantity_needed=payload.quantity_needed,
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    award_points(db, current_user.id, "quote_sent", f'Sent quote request for "{listing.title}"', category="marketplace")

    # Fire email + WhatsApp notifications in background
    seller = db.query(User).filter(User.id == listing.owner_id).first()
    if seller:
        background_tasks.add_task(
            send_quote_received,
            seller.email, seller.company_name, current_user.company_name,
            listing.title, payload.quantity_needed, payload.message, quote.id
        )
        if seller.phone:
            background_tasks.add_task(
                wa_new_quote_alert,
                seller.phone, seller.company_name, current_user.company_name,
                listing.title, payload.quantity_needed, quote.id
            )
    background_tasks.add_task(
        send_quote_confirmation,
        current_user.email, current_user.company_name,
        seller.company_name if seller else "Seller", listing.title, quote.id
    )
    return enrich_quote(quote)

@router.get("/sent", response_model=List[QuoteOut])
def my_sent_quotes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quotes = db.query(QuoteRequest).filter(QuoteRequest.buyer_id == current_user.id)\
               .order_by(QuoteRequest.created_at.desc()).all()
    return [enrich_quote(q) for q in quotes]

@router.get("/received", response_model=List[QuoteOut])
def my_received_quotes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quotes = db.query(QuoteRequest).filter(QuoteRequest.seller_id == current_user.id)\
               .order_by(QuoteRequest.created_at.desc()).all()
    return [enrich_quote(q) for q in quotes]

@router.put("/{quote_id}/status", response_model=QuoteOut)
def update_quote_status(
    quote_id: int,
    payload: QuoteStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quote = db.query(QuoteRequest).filter(QuoteRequest.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.seller_id != current_user.id and quote.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your quote")
    allowed_transitions = {
        "pending":  ["accepted", "rejected"],
        "accepted": ["completed", "rejected"],
    }
    if payload.status not in allowed_transitions.get(quote.status, []):
        raise HTTPException(status_code=400, detail=f"Cannot transition from {quote.status} to {payload.status}")
    quote.status = payload.status
    db.commit()

    listing_title = quote.listing.title if quote.listing else "waste exchange"
    buyer  = db.query(User).filter(User.id == quote.buyer_id).first()
    seller = db.query(User).filter(User.id == quote.seller_id).first()

    if payload.status == "completed":
        award_points(db, quote.seller_id, "exchange_completed",
                     f'Exchange completed — "{listing_title}"', category="exchange")
        award_points(db, quote.buyer_id, "exchange_completed",
                     f'Exchange completed — "{listing_title}"', category="exchange")
        if buyer:
            background_tasks.add_task(
                send_quote_status_update, buyer.email, buyer.company_name, listing_title, "completed", quote.id
            )
            if buyer.phone:
                background_tasks.add_task(wa_exchange_completed, buyer.phone, buyer.company_name, listing_title, quote.id)
        if seller:
            background_tasks.add_task(
                send_quote_status_update, seller.email, seller.company_name, listing_title, "completed", quote.id
            )
            if seller.phone:
                background_tasks.add_task(wa_exchange_completed, seller.phone, seller.company_name, listing_title, quote.id)
    elif payload.status == "accepted" and buyer:
        background_tasks.add_task(
            send_quote_status_update, buyer.email, buyer.company_name, listing_title, "accepted", quote.id
        )
        if buyer.phone:
            background_tasks.add_task(
                wa_quote_accepted, buyer.phone, buyer.company_name,
                seller.company_name if seller else "", listing_title, quote.id
            )
    elif payload.status == "rejected" and buyer:
        background_tasks.add_task(
            send_quote_status_update, buyer.email, buyer.company_name, listing_title, "rejected", quote.id
        )
        if buyer.phone:
            background_tasks.add_task(
                wa_quote_rejected, buyer.phone, listing_title,
                seller.company_name if seller else "", quote.id
            )

    db.refresh(quote)
    return enrich_quote(quote)

@router.post("/{quote_id}/rate", response_model=QuoteOut)
def rate_exchange(
    quote_id: int,
    payload: RatingSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quote = db.query(QuoteRequest).filter(QuoteRequest.id == quote_id, QuoteRequest.status == "completed").first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found or not completed")
    if payload.role == "buyer" and quote.buyer_id == current_user.id:
        quote.buyer_rating = payload.rating
        award_points(db, quote.seller_id, "rating_received",
                     f"Received {payload.rating}★ rating", category="rating")
    elif payload.role == "seller" and quote.seller_id == current_user.id:
        quote.seller_rating = payload.rating
        award_points(db, quote.buyer_id, "rating_received",
                     f"Received {payload.rating}★ rating", category="rating")
    else:
        raise HTTPException(status_code=403, detail="Cannot rate this exchange")
    db.commit()
    db.refresh(quote)
    return enrich_quote(quote)
