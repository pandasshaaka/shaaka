from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from time import time
import random
import logging

logging.basicConfig(level=logging.INFO)
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# In-memory OTP storage
otp_store: dict[str, tuple[str, float]] = {}

class SendOtpRequest(BaseModel):
    mobile_no: str

class VerifyOtpRequest(BaseModel):
    mobile_no: str
    otp_code: str = Field(min_length=4)

@app.post("/auth/send-otp")
def send_otp(payload: SendOtpRequest):
    code = f"{random.randint(100000, 999999)}"
    expiry = time() + 300
    otp_store[payload.mobile_no] = (code, expiry)
    logging.info(f"OTP for {payload.mobile_no}: {code}")
    return {"sent": True}

@app.post("/auth/verify-otp")
def verify_otp(payload: VerifyOtpRequest):
    logging.info(f"OTP verification attempt for mobile: {payload.mobile_no}")
    
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
    
    logging.info(f"OTP verification successful for mobile: {payload.mobile_no}")
    del otp_store[payload.mobile_no]
    return {"verified": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_main:app", host="0.0.0.0", port=8002, reload=True)