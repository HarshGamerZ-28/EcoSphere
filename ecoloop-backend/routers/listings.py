from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from models.database import get_db, Listing, User
from models.schemas import ListingCreate, ListingOut, ListingUpdate
from core.auth import get_current_user, get_optional_user
from core.green_score import award_points

router = APIRouter(prefix="/listings", tags=["Listings"])

@router.get("/", response_model=List[ListingOut])
def get_listings(
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(Listing).filter(Listing.is_active == True)
    if category:
        q = q.filter(Listing.category == category)
    if location:
        q = q.filter(Listing.location.ilike(f"%{location}%"))
    if search:
        q = q.filter(
            Listing.title.ilike(f"%{search}%") |
            Listing.description.ilike(f"%{search}%")
        )
    listings = q.order_by(Listing.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for l in listings:
        out = ListingOut.model_validate(l)
        if l.owner:
            out.company_name = l.owner.company_name
        result.append(out)
    return result

@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    l = db.query(Listing).filter(Listing.id == listing_id, Listing.is_active == True).first()
    if not l:
        raise HTTPException(status_code=404, detail="Listing not found")
    out = ListingOut.model_validate(l)
    if l.owner:
        out.company_name = l.owner.company_name
    return out

@router.post("/", response_model=ListingOut, status_code=201)
def create_listing(
    payload: ListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    green_pts = max(20, int(payload.price_per_unit * 0.8 + 15))
    listing = Listing(
        **payload.model_dump(),
        owner_id=current_user.id,
        green_pts_value=green_pts,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    # Award green points
    award_points(db, current_user.id, "waste_listed",
                 f'Listed "{listing.title}" on marketplace',
                 custom_pts=45, category="listing")
    out = ListingOut.model_validate(listing)
    out.company_name = current_user.company_name
    return out

@router.put("/{listing_id}", response_model=ListingOut)
def update_listing(
    listing_id: int,
    payload: ListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    listing = db.query(Listing).filter(Listing.id == listing_id, Listing.owner_id == current_user.id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or not yours")
    for key, val in payload.model_dump(exclude_none=True).items():
        setattr(listing, key, val)
    db.commit()
    db.refresh(listing)
    out = ListingOut.model_validate(listing)
    out.company_name = current_user.company_name
    return out

@router.delete("/{listing_id}", status_code=204)
def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    listing = db.query(Listing).filter(Listing.id == listing_id, Listing.owner_id == current_user.id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or not yours")
    listing.is_active = False
    db.commit()

@router.get("/my/listings", response_model=List[ListingOut])
def my_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    listings = db.query(Listing).filter(
        Listing.owner_id == current_user.id,
        Listing.is_active == True
    ).order_by(Listing.created_at.desc()).all()
    result = []
    for l in listings:
        out = ListingOut.model_validate(l)
        out.company_name = current_user.company_name
        result.append(out)
    return result
