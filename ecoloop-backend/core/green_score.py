from sqlalchemy.orm import Session
from models.database import GreenScore, ScoreEvent, User
from datetime import datetime

TIER_THRESHOLDS = {"Bronze": 0, "Silver": 500, "Gold": 1000}

POINT_RULES = {
    "waste_listed":      45,
    "exchange_completed": 120,
    "compliance_upload":  40,
    "rating_received":    20,
    "ai_matcher_used":    25,
    "profile_completed":  30,
    "quote_sent":          5,
    "co2_per_100kg":      10,
}

def get_or_create_score(db: Session, user_id: int) -> GreenScore:
    score = db.query(GreenScore).filter(GreenScore.user_id == user_id).first()
    if not score:
        score = GreenScore(user_id=user_id, total_score=0, tier="Bronze")
        db.add(score)
        db.commit()
        db.refresh(score)
    return score

def award_points(db: Session, user_id: int, event_type: str, reason: str,
                 custom_pts: int | None = None, category: str | None = None) -> int:
    pts = custom_pts if custom_pts is not None else POINT_RULES.get(event_type, 10)
    score = get_or_create_score(db, user_id)

    # Route pts to correct sub-bucket
    if event_type == "waste_listed":
        score.waste_listed_pts = min(score.waste_listed_pts + pts, 200)
    elif event_type == "exchange_completed":
        score.exchange_pts += pts
    elif event_type in ("compliance_upload", "profile_completed"):
        score.compliance_pts = min(score.compliance_pts + pts, 100)
    elif event_type == "rating_received":
        score.rating_pts = min(score.rating_pts + pts, 100)
    elif event_type == "co2_per_100kg":
        score.co2_pts = min(score.co2_pts + pts, 200)
    else:
        score.waste_listed_pts += pts  # default bucket

    score.total_score += pts
    score.tier = compute_tier(score.total_score)
    score.updated_at = datetime.utcnow()

    event = ScoreEvent(user_id=user_id, points=pts, reason=reason, category=category)
    db.add(event)
    db.commit()
    db.refresh(score)
    return pts

def compute_tier(score: int) -> str:
    if score >= 1000:
        return "Gold"
    if score >= 500:
        return "Silver"
    return "Bronze"

def get_score_summary(db: Session, user_id: int) -> dict:
    score = get_or_create_score(db, user_id)
    events = (db.query(ScoreEvent)
              .filter(ScoreEvent.user_id == user_id)
              .order_by(ScoreEvent.created_at.desc())
              .limit(10).all())
    next_tier_pts = 1000 if score.total_score >= 1000 else (1000 if score.tier == "Silver" else 500)
    pts_to_next = max(0, next_tier_pts - score.total_score)
    return {
        "score": score,
        "events": events,
        "pts_to_next_tier": pts_to_next,
        "next_tier": "Gold" if score.tier == "Silver" else ("Max" if score.tier == "Gold" else "Silver"),
    }
