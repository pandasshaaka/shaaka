from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy.orm import Session
from time import time
import random
import logging
from common.db import SessionLocal, ensure_engine
from common.models import UserProfile
from common.security import hash_password, verify_password, create_access_token


router = APIRouter()


def get_db():
    ensure_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

##
otp_store: dict[str, tuple[str, float]] = {}


class SendOtpRequest(BaseModel):
    mobile_no: str


class RegisterRequest(BaseModel):
    full_name: str
    mobile_no: str
    password: str
    gender: str | None = None
    category: Literal['Vendor', 'Women Merchant', 'Customer']
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    profile_photo_url: str | None = None
    profile_photo_data: str | None = None  # Base64 encoded image data
    profile_photo_mime_type: str | None = None  # e.g., 'image/jpeg', 'image/png'
    otp_code: str = Field(min_length=4)


class LoginRequest(BaseModel):
    mobile_no: str
    password: str


@router.post("/send-otp")
def send_otp(payload: SendOtpRequest):
    code = f"{random.randint(100000, 999999)}"
    expiry = time() + 300
    otp_store[payload.mobile_no] = (code, expiry)
    logging.info(f"OTP for {payload.mobile_no}: {code}")
    return {"sent": True}


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    logging.info(f"Registration attempt for mobile: {payload.mobile_no}")
    
    stored = otp_store.get(payload.mobile_no)
    if not stored:
        logging.warning(f"OTP not found for mobile: {payload.mobile_no}")
        raise HTTPException(status_code=400, detail="otp_required")
    
    code, expiry = stored
    if time() > expiry:
        del otp_store[payload.mobile_no]
        logging.warning(f"OTP expired for mobile: {payload.mobile_no}")
        raise HTTPException(status_code=400, detail="otp_expired")
    
    if payload.otp_code != code:
        logging.warning(f"Invalid OTP for mobile: {payload.mobile_no}. Expected: {code}, Got: {payload.otp_code}")
        raise HTTPException(status_code=400, detail="otp_invalid")
    
    logging.info(f"OTP validation successful for mobile: {payload.mobile_no}")
    
    existing = db.query(UserProfile).filter(UserProfile.mobile_no == payload.mobile_no).first()
    if existing:
        logging.warning(f"Mobile number already exists: {payload.mobile_no}")
        raise HTTPException(status_code=400, detail="mobile_exists")
    
    logging.info(f"No existing user found for mobile: {payload.mobile_no}")
    
    hashed = hash_password(payload.password)
    logging.info(f"Password hashed successfully for mobile: {payload.mobile_no}")
    
    obj = UserProfile(
        full_name=payload.full_name,
        mobile_no=payload.mobile_no,
        password=hashed,
        gender=payload.gender,
        category=payload.category,
        address_line=payload.address_line,
        city=payload.city,
        state=payload.state,
        country=payload.country,
        pincode=payload.pincode,
        latitude=payload.latitude,
        longitude=payload.longitude,
        profile_photo_url=payload.profile_photo_url,
    )
    
    # Handle profile photo data if provided
    if payload.profile_photo_data and payload.profile_photo_mime_type:
        try:
            # Decode base64 data and store in database
            import base64
            image_data = base64.b64decode(payload.profile_photo_data)
            obj.set_profile_photo(image_data, payload.profile_photo_mime_type)
            logging.info(f"Profile photo stored in database for mobile: {payload.mobile_no}")
        except Exception as e:
            logging.error(f"Failed to process profile photo for mobile: {payload.mobile_no}: {e}")
            # Continue with registration even if photo processing fails
    
    logging.info(f"Creating user object for mobile: {payload.mobile_no}")
    
    try:
        db.add(obj)
        logging.info(f"User object added to session for mobile: {payload.mobile_no}")
        
        db.commit()
        logging.info(f"Database commit successful for mobile: {payload.mobile_no}")
        
        db.refresh(obj)
        logging.info(f"User object refreshed from database for mobile: {payload.mobile_no}")
        
        del otp_store[payload.mobile_no]
        logging.info(f"OTP removed from store for mobile: {payload.mobile_no}")
        
        logging.info(f"Registration successful for mobile: {payload.mobile_no}, user_id: {obj.id}")
        return {"id": str(obj.id), "mobile_no": obj.mobile_no}
        
    except Exception as e:
        logging.error(f"Database error during registration for mobile: {payload.mobile_no}, error: {str(e)}")
        db.rollback()
        logging.error(f"Database rollback executed for mobile: {payload.mobile_no}")
        raise HTTPException(status_code=500, detail="database_error")


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    obj = db.query(UserProfile).filter(UserProfile.mobile_no == payload.mobile_no).first()
    if not obj:
        raise HTTPException(status_code=400, detail="invalid_credentials")
    if not verify_password(payload.password, obj.password):
        raise HTTPException(status_code=400, detail="invalid_credentials")
    token = create_access_token(str(obj.id), obj.category)
    return {"access_token": token, "token_type": "bearer", "category": obj.category}
