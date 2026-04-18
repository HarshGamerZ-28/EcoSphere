from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import ChatMessage, QuoteRequest, User, get_db
from models.schemas import ChatMessageCreate, ChatMessageOut, QuoteUpdate
from core.auth import get_current_user
from datetime import datetime

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
    if quote.status != "accepted":
        raise HTTPException(status_code=400, detail="Can only chat on accepted quotes")
    
    # Verify sender is buyer or seller in this quote
    if current_user.id not in [quote.buyer_id, quote.seller_id]:
        raise HTTPException(status_code=403, detail="Not authorized for this quote")
    
    # Create message
    msg = ChatMessage(
        quote_id=payload.quote_id,
        sender_id=current_user.id,
        receiver_id=payload.receiver_id,
        message=payload.message
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

# ── Get Conversation ───────────────────────────────
@router.get("/conversation/{quote_id}", response_model=list[ChatMessageOut])
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
    messages = db.query(ChatMessage).filter(ChatMessage.quote_id == quote_id).all()
    for msg in messages:
        if msg.receiver_id == current_user.id and not msg.is_read:
            msg.is_read = True
    db.commit()
    
    return messages

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
