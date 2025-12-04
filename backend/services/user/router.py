from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from common.db import SessionLocal, ensure_engine
from common.models import UserProfile
from common.security import decode_token


router = APIRouter()
security = HTTPBearer()


def get_db():
    ensure_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/me")
def me(creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    data = decode_token(creds.credentials)
    uid = data.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="invalid_token")
    obj = db.query(UserProfile).filter(UserProfile.id == uid).first()
    if not obj:
        raise HTTPException(status_code=404, detail="not_found")
    return {
        "id": str(obj.id),
        "full_name": obj.full_name,
        "mobile_no": obj.mobile_no,
        "gender": obj.gender,
        "category": obj.category,
        "address_line": obj.address_line,
        "city": obj.city,
        "state": obj.state,
        "country": obj.country,
        "pincode": obj.pincode,
        "latitude": float(obj.latitude) if obj.latitude is not None else None,
        "longitude": float(obj.longitude) if obj.longitude is not None else None,
        "profile_photo_url": obj.profile_photo_url,
        "profile_photo_data": obj.profile_photo_data,  # Base64 encoded image data
        "profile_photo_mime_type": obj.profile_photo_mime_type,
    }
