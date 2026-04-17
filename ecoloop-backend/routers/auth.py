from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.database import get_db, User, GreenScore
from models.schemas import UserRegister, UserLogin, UserOut, Token
from core.auth import hash_password, verify_password, create_access_token, get_current_user
from core.green_score import award_points

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=Token, status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        company_name=payload.company_name,
        gst_number=payload.gst_number,
        phone=payload.phone,
        location=payload.location,
        industry=payload.industry,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Seed green score
    score = GreenScore(user_id=user.id, total_score=0, tier="Bronze")
    db.add(score)
    db.commit()
    # Award profile-complete points
    award_points(db, user.id, "profile_completed", "Company profile created", category="onboarding")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.model_validate(user))

@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.is_active == True).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.model_validate(user))

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserOut)
def update_profile(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed = {"company_name","phone","location","industry","gst_number"}
    for key, val in data.items():
        if key in allowed and val is not None:
            setattr(current_user, key, val)
    db.commit()
    db.refresh(current_user)
    return current_user
