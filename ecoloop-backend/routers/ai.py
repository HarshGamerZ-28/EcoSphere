from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.database import get_db, AIMatchLog, User
from models.schemas import AIMatchRequest, AIMatchResponse, AIDescriptionRequest, AIInsightRequest
from core.auth import get_optional_user
from core.gemini import ai_match_waste, ai_generate_description, ai_waste_insights, get_fallback_matches
from core.green_score import award_points
import json

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/match", response_model=AIMatchResponse)
async def match_waste(
    payload: AIMatchRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user)
):
    matches = []
    used_real_ai = False
    reasoning = ""

    try:
        raw_matches = await ai_match_waste(
            payload.waste_name, payload.category,
            payload.quantity or "", payload.description or ""
        )
        matches = raw_matches
        used_real_ai = True
        reasoning = matches[0].get("reasoning","") if matches else ""
    except Exception as e:
        matches = get_fallback_matches(payload.category)
        reasoning = f"AI currently using optimized fallback matches ({str(e)[:40]})."

    # Log match
    log = AIMatchLog(
        user_id=current_user.id if current_user else None,
        waste_name=payload.waste_name,
        waste_category=payload.category,
        quantity=payload.quantity,
        matches_json=json.dumps(matches),
        used_real_ai=used_real_ai,
    )
    db.add(log)
    db.commit()

    # Award green points to authenticated user
    if current_user:
        award_points(db, current_user.id, "ai_matcher_used",
                     f'Used AI Matcher for {payload.waste_name}', category="ai")

    # Normalise response
    normalised = []
    for m in matches:
        normalised.append({
            "company":   m.get("company",""),
            "type":      m.get("type",""),
            "location":  m.get("location",""),
            "score":     int(m.get("score", 80)),
            "reasoning": m.get("reasoning",""),
            "co2_saved": m.get("co2_saved","~1 tonne CO₂"),
            "price_range": m.get("price_range","₹XX/kg"),
            "tags":      m.get("tags",[]),
            "compliance":m.get("compliance","GST Reg."),
        })

    return AIMatchResponse(
        matches=normalised,
        used_real_ai=used_real_ai,
        reasoning_summary=reasoning
    )

@router.post("/generate-description")
async def generate_description(payload: AIDescriptionRequest):
    try:
        desc = await ai_generate_description(payload.waste_name, payload.category)
        return {"description": desc}
    except Exception as e:
        return {"description": "", "error": str(e)}

@router.post("/insights")
async def waste_insights(payload: AIInsightRequest):
    try:
        insights = await ai_waste_insights(payload.waste_name, payload.category)
        return {"insights": insights}
    except Exception as e:
        return {"insights": "", "error": str(e)}
