from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from common.db import SessionLocal, ensure_engine
from common.models import UserProfile
from common.security import decode_token
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
security = HTTPBearer()

@router.get("/test")
def test_endpoint():
    return {"message": "User service is working"}

@router.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    try:
        # Test database connection
        result = db.execute("SELECT 1").fetchone()
        return {"message": "Database connection successful", "result": result[0]}
    except Exception as e:
        return {"message": "Database connection failed", "error": str(e)}

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    mobile_no: Optional[str] = None
    gender: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    profile_photo_data: Optional[str] = None
    profile_photo_mime_type: Optional[str] = None


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


@router.post("/update-profile")
def update_profile(
    request: ProfileUpdateRequest,
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        print(f"Update profile called with token: {creds.credentials[:20]}...")
        data = decode_token(creds.credentials)
        uid = data.get("sub")
        print(f"Decoded UID: {uid}")
        if not uid:
            raise HTTPException(status_code=401, detail="invalid_token")
        
        print(f"Request data: {request}")
        print(f"Full name: {request.full_name}")
        print(f"Mobile: {request.mobile_no}")
        
        obj = db.query(UserProfile).filter(UserProfile.id == uid).first()
        if not obj:
            raise HTTPException(status_code=404, detail="not_found")
        
        # Update profile fields only if provided
        if request.full_name is not None:
            obj.full_name = request.full_name
        if request.mobile_no is not None:
            obj.mobile_no = request.mobile_no
        if request.gender is not None:
            obj.gender = request.gender
        if request.address_line is not None:
            obj.address_line = request.address_line
        if request.city is not None:
            obj.city = request.city
        if request.state is not None:
            obj.state = request.state
        if request.country is not None:
            obj.country = request.country
        if request.pincode is not None:
            obj.pincode = request.pincode
        
        # Update profile photo if provided
        if request.profile_photo_data:
            obj.profile_photo_data = request.profile_photo_data
            obj.profile_photo_mime_type = request.profile_photo_mime_type or 'image/jpeg'
            obj.profile_photo_url = f"data:{obj.profile_photo_mime_type};base64,{request.profile_photo_data}"
        
        db.commit()
        db.refresh(obj)
        
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
            "profile_photo_data": obj.profile_photo_data,
            "profile_photo_mime_type": obj.profile_photo_mime_type,
        }
    except Exception as e:
        print(f"Error in update_profile: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
