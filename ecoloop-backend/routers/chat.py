from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from models.database import ChatMessage, QuoteRequest, User, get_db, ProgressUpdate
from models.schemas import (
    ChatMessageCreate, ChatMessageOut, ChatConversationOut, 
    ProgressUpdateCreate, ProgressUpdateOut
)
from core.auth import get_current_user
from datetime import datetime
from typing import List

router = APIRouter(prefix="/chat", tags=["Chat"])

# ── Send Message ───────────────────────────────────
@router.post("/send", response_model=ChatMessageOut)
async def send_message(
    payload: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a chat message in an accepted quote conversation"""
    # Verify quote exists and is accepted
    quote = db.query(QuoteRequest).filter(QuoteRequest.id == payload.quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.status not in ["accepted", "completed"]:
        raise HTTPException(status_code=400, detail="Can only chat on accepted/completed quotes")
    
    # Verify sender is buyer or seller in this quote
    if current_user.id not in [quote.buyer_id, quote.seller_id]:
        raise HTTPException(status_code=403, detail="Not authorized for this quote")
    
    # Determine receiver
    receiver_id = quote.seller_id if current_user.id == quote.buyer_id else quote.buyer_id

    # Create message
    msg = ChatMessage(
        quote_id=payload.quote_id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message=payload.message
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

# ── Get Conversations ─────────────────────────────
@router.get("/conversations", response_model=List[ChatConversationOut])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of all active chat conversations for the user"""
    # Find all accepted/completed quotes where user is involved
    quotes = db.query(QuoteRequest).filter(
        and_(
            or_(QuoteRequest.buyer_id == current_user.id, QuoteRequest.seller_id == current_user.id),
            or_(QuoteRequest.status == "accepted", QuoteRequest.status == "completed")
        )
    ).all()

    results = []
    for q in quotes:
        other_user_id = q.seller_id if q.buyer_id == current_user.id else q.buyer_id
        other_user = db.query(User).filter(User.id == other_user_id).first()
        
        last_msg = db.query(ChatMessage).filter(ChatMessage.quote_id == q.id)\
                     .order_by(ChatMessage.created_at.desc()).first()
        
        unread = db.query(ChatMessage).filter(
            ChatMessage.quote_id == q.id,
            ChatMessage.receiver_id == current_user.id,
            ChatMessage.is_read == False
        ).count()

        results.append(ChatConversationOut(
            user_id=other_user_id,
            user_name=other_user.company_name if other_user else "Unknown Company",
            last_message=last_msg.message if last_msg else None,
            unread_count=unread,
            quote_id=q.id
        ))
    
    return results

# ── Get Conversation ───────────────────────────────
@router.get("/conversation/{quote_id}", response_model=List[ChatMessageOut])
async def get_conversation(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages in a quote conversation"""
    quote = db.query(QuoteRequest).filter(QuoteRequest.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Verify user is involved in this quote
    if current_user.id not in [quote.buyer_id, quote.seller_id]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get all messages and mark as read
    messages = db.query(ChatMessage).filter(ChatMessage.quote_id == quote_id).order_by(ChatMessage.created_at.asc()).all()
    
    db.query(ChatMessage).filter(
        ChatMessage.quote_id == quote_id,
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False
    ).update({"is_read": True})
    db.commit()
    
    return messages

# ── Progress Tracking ──────────────────────────────
@router.get("/progress/{quote_id}", response_model=List[ProgressUpdateOut])
async def get_progress(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all progress updates for a quote"""
    quote = db.query(QuoteRequest).filter(QuoteRequest.id == quote_id).first()
    if not quote or (quote.buyer_id != current_user.id and quote.seller_id != current_user.id):
        raise HTTPException(status_code=404, detail="Progress not found")
    
    updates = db.query(ProgressUpdate).filter(ProgressUpdate.quote_id == quote_id).order_by(ProgressUpdate.created_at.asc()).all()
    return updates

@router.post("/progress/{quote_id}", response_model=ProgressUpdateOut)
async def add_progress(
    quote_id: int,
    payload: ProgressUpdateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new progress stage update (only seller can update progress)"""
    quote = db.query(QuoteRequest).filter(QuoteRequest.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # Only seller can update progress stages in this workflow
    if quote.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the seller can update deal progress")
    
    update = ProgressUpdate(
        quote_id=quote_id,
        stage=payload.stage,
        note=payload.note
    )
    db.add(update)
    db.commit()
    db.refresh(update)
    return update

# ── Unread Count ───────────────────────────────────
@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of unread messages"""
    unread = db.query(ChatMessage).filter(
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False
    ).count()
    return {"unread_count": unread}
