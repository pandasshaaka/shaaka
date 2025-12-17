from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from common.db import SessionLocal, ensure_engine
from common.models import Donation, DeliveryPartner, DeliveryAssignment, Notification
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
security = HTTPBearer()

def get_db():
    ensure_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DonationCreate(BaseModel):
    food_name: str
    quantity: int
    description: Optional[str] = None
    pickup_address: str

@router.post("/donations")
def create_donation(payload: DonationCreate, creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    from common.security import decode_token
    data = decode_token(creds.credentials)
    uid = data.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="invalid_token")
    obj = Donation(donor_id=uid, food_name=payload.food_name, quantity=payload.quantity, description=payload.description, pickup_address=payload.pickup_address, status="PENDING")
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": str(obj.id)}

@router.get("/donations")
def list_donations(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Donation)
    if status:
        q = q.filter(Donation.status == status)
    rows = q.order_by(Donation.created_at.desc()).all()
    return [{"id": str(r.id), "donor_id": str(r.donor_id), "food_name": r.food_name, "quantity": r.quantity, "description": r.description, "pickup_address": r.pickup_address, "status": r.status, "created_at": str(r.created_at)} for r in rows]

class DonationStatusUpdate(BaseModel):
    status: str

@router.patch("/donations/{donation_id}/status")
def update_donation_status(donation_id: str, payload: DonationStatusUpdate, db: Session = Depends(get_db)):
    obj = db.query(Donation).filter(Donation.id == donation_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="not_found")
    obj.status = payload.status
    db.commit()
    return {"ok": True}

class PartnerCreate(BaseModel):
    vehicle_type: str
    license_number: str

@router.post("/delivery-partners")
def create_partner(payload: PartnerCreate, creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    from backend.common.security import decode_token
    data = decode_token(creds.credentials)
    uid = data.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="invalid_token")
    obj = DeliveryPartner(user_id=uid, vehicle_type=payload.vehicle_type, license_number=payload.license_number, is_available=True)
    db.merge(obj)
    db.commit()
    return {"user_id": uid}

@router.get("/delivery-partners")
def list_partners(available: Optional[bool] = None, db: Session = Depends(get_db)):
    q = db.query(DeliveryPartner)
    if available is not None:
        q = q.filter(DeliveryPartner.is_available == available)
    rows = q.all()
    return [{"user_id": str(r.user_id), "vehicle_type": r.vehicle_type, "license_number": r.license_number, "is_available": bool(r.is_available)} for r in rows]

class AssignmentCreate(BaseModel):
    delivery_partner_id: str
    order_id: Optional[str] = None
    donation_id: Optional[str] = None
    status: str

@router.post("/delivery-assignments")
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db)):
    if not payload.order_id and not payload.donation_id:
        raise HTTPException(status_code=400, detail="target_required")
    obj = DeliveryAssignment(delivery_partner_id=payload.delivery_partner_id, order_id=payload.order_id, donation_id=payload.donation_id, status=payload.status)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": str(obj.id)}

@router.get("/delivery-assignments")
def list_assignments(delivery_partner_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(DeliveryAssignment)
    if delivery_partner_id:
        q = q.filter(DeliveryAssignment.delivery_partner_id == delivery_partner_id)
    rows = q.order_by(DeliveryAssignment.assigned_at.desc()).all()
    return [{"id": str(r.id), "delivery_partner_id": str(r.delivery_partner_id), "order_id": str(r.order_id) if r.order_id else None, "donation_id": str(r.donation_id) if r.donation_id else None, "status": r.status, "assigned_at": str(r.assigned_at)} for r in rows]

class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str

@router.post("/notifications")
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    obj = Notification(user_id=payload.user_id, title=payload.title, message=payload.message, is_read=False)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": str(obj.id)}

@router.get("/notifications")
def list_notifications(user_id: str, db: Session = Depends(get_db)):
    rows = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
    return [{"id": str(r.id), "title": r.title, "message": r.message, "is_read": bool(r.is_read), "created_at": str(r.created_at)} for r in rows]

@router.post("/notifications/{notification_id}/mark-read")
def mark_notification_read(notification_id: str, db: Session = Depends(get_db)):
    obj = db.query(Notification).filter(Notification.id == notification_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="not_found")
    obj.is_read = True
    db.commit()
    return {"ok": True}
