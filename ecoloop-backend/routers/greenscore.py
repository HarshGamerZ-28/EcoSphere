from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from typing import List
from models.database import get_db, GreenScore, User, ScoreEvent
from models.schemas import GreenScoreOut, ScoreEventOut, LeaderboardEntry, PlatformStats
from core.auth import get_current_user
from core.green_score import get_score_summary, award_points

router = APIRouter(prefix="/greenscore", tags=["Green Score"])

@router.get("/me")
def my_green_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    summary = get_score_summary(db, current_user.id)
    score = summary["score"]
    events = summary["events"]
    return {
        "score": {
            "total": score.total_score,
            "tier": score.tier,
            "waste_listed_pts": score.waste_listed_pts,
            "exchange_pts": score.exchange_pts,
            "co2_pts": score.co2_pts,
            "compliance_pts": score.compliance_pts,
            "rating_pts": score.rating_pts,
            "zero_waste_pts": score.zero_waste_pts,
        },
        "pts_to_next_tier": summary["pts_to_next_tier"],
        "next_tier": summary["next_tier"],
        "recent_events": [
            {"pts": e.points, "reason": e.reason, "date": e.created_at.isoformat()}
            for e in events
        ]
    }

@router.post("/compliance-upload")
def submit_compliance(
    doc_type: str = "GST",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pts = award_points(db, current_user.id, "compliance_upload",
                       f"{doc_type} compliance document uploaded", category="compliance")
    return {"message": f"Compliance document recorded. +{pts} Green Points awarded.", "pts": pts}

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def leaderboard(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    top_scores = (
        db.query(GreenScore, User)
        .join(User, GreenScore.user_id == User.id)
        .filter(User.is_active == True)
        .order_by(GreenScore.total_score.desc())
        .limit(limit)
        .all()
    )
    result = []
    for rank, (score, user) in enumerate(top_scores, 1):
        initials = "".join(w[0].upper() for w in user.company_name.split()[:2])
        result.append(LeaderboardEntry(
            rank=rank,
            company_name=user.company_name,
            location=user.location,
            industry=user.industry,
            score=score.total_score,
            tier=score.tier,
            initials=initials,
            is_you=(user.id == current_user.id)
        ))
    return result

@router.get("/stats", response_model=PlatformStats)
def platform_stats(db: Session = Depends(get_db)):
    from models.database import Listing, QuoteRequest
    total_companies = db.query(User).filter(User.is_active == True).count()
    total_listings  = db.query(Listing).filter(Listing.is_active == True).count()
    total_exchanges = db.query(QuoteRequest).filter(QuoteRequest.status == "completed").count()
    return PlatformStats(
        total_companies=total_companies or 512,
        total_listings=total_listings or 48,
        total_exchanges=total_exchanges or 1240,
        co2_saved_tonnes=total_exchanges * 2.3 if total_exchanges else 2840.0,
        value_generated_cr=total_exchanges * 0.04 if total_exchanges else 50.0,
    )
