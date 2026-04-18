from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import QuoteRequest, Listing, User, get_db
from models.schemas import QuoteUpdate
from core.auth import get_current_user
from core.green_score import award_points
from datetime import datetime

router = APIRouter(prefix="/quotes", tags=["Quotes"])

# ── Get My Quotes (Sent & Received) ────────────────
@router.get("/my-quotes")
async def get_my_quotes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all quotes (sent and received)"""
    sent = db.query(QuoteRequest).filter(QuoteRequest.buyer_id == current_user.id).all()
    received = db.query(QuoteRequest).filter(QuoteRequest.seller_id == current_user.id).all()
    
    sent_data = [{
        "id": q.id,
        "type": "sent",
        "listing_id": q.listing_id,
        "listing_title": q.listing.title,
        "buyer_company": current_user.company_name,
        "seller_company": q.seller.company_name,
        "seller_id": q.seller_id,
        "status": q.status,
        "message": q.message,
        "quantity_needed": q.quantity_needed,
        "created_at": q.created_at,
        "updated_at": q.updated_at
    } for q in sent]
    
    received_data = [{
        "id": q.id,
        "type": "received",
        "listing_id": q.listing_id,
        "listing_title": q.listing.title,
        "buyer_company": q.buyer.company_name,
        "buyer_id": q.buyer_id,
        "seller_company": current_user.company_name,
        "status": q.status,
        "message": q.message,
        "quantity_needed": q.quantity_needed,
        "created_at": q.created_at,
        "updated_at": q.updated_at
    } for q in received]
    
    return {"sent": sent_data, "received": received_data}

# ── Update Quote Status ────────────────────────────
@router.put("/{quote_id}/status")
async def update_quote_status(
    quote_id: int,
    payload: QuoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update quote status (accept/reject)"""
    quote = db.query(QuoteRequest).filter(QuoteRequest.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Only seller can accept/reject
    if quote.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only seller can update quote status")
    
    # Validate status
    valid_statuses = ["accepted", "rejected", "completed"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    old_status = quote.status
    quote.status = payload.status
    quote.updated_at = datetime.utcnow()
    
    # Award points for acceptance
    if payload.status == "accepted":
        award_points(db, current_user.id, "quote_accepted", 
                    f"Accepted quote for {quote.listing.title}", category="exchange")
        # Also award to buyer
        award_points(db, quote.buyer_id, "quote_accepted_buyer",
                    f"Quote accepted for {quote.listing.title}", category="exchange")
    
    db.commit()
    db.refresh(quote)
    
    return {
        "id": quote.id,
        "old_status": old_status,
        "new_status": quote.status,
        "message": f"Quote {payload.status} successfully"
    }

# ── Get Quote Details ──────────────────────────────
@router.get("/{quote_id}")
async def get_quote_detail(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed quote information"""
    quote = db.query(QuoteRequest).filter(QuoteRequest.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Verify user is involved
    if current_user.id not in [quote.buyer_id, quote.seller_id]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "id": quote.id,
        "listing": {
            "id": quote.listing.id,
            "title": quote.listing.title,
            "category": quote.listing.category,
            "quantity": quote.listing.quantity,
            "price_per_unit": quote.listing.price_per_unit,
            "unit": quote.listing.unit,
            "location": quote.listing.location,
            "description": quote.listing.description
        },
        "buyer": {
            "id": quote.buyer.id,
            "company_name": quote.buyer.company_name,
            "location": quote.buyer.location,
            "phone": quote.buyer.phone
        },
        "seller": {
            "id": quote.seller.id,
            "company_name": quote.seller.company_name,
            "location": quote.seller.location,
            "phone": quote.seller.phone
        },
        "message": quote.message,
        "quantity_needed": quote.quantity_needed,
        "status": quote.status,
        "created_at": quote.created_at,
        "updated_at": quote.updated_at
    }
