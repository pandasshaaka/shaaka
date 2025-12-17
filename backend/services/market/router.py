from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from common.db import SessionLocal, ensure_engine
from common.models import Category, Store, Product, ProductImage, Cart, CartItem, Order, OrderItem, Payment, Review, UserProfile
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()
security = HTTPBearer()

def get_db():
    ensure_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CategoryCreate(BaseModel):
    name: str

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    rows = db.query(Category).order_by(Category.name.asc()).all()
    return [{"id": str(r.id), "name": r.name} for r in rows]

@router.post("/categories")
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(Category).filter(Category.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="exists")
    obj = Category(name=payload.name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": str(obj.id), "name": obj.name}

class StoreCreate(BaseModel):
    store_name: str
    store_type: str
    description: Optional[str] = None
    is_open: Optional[bool] = True

@router.get("/stores")
def list_stores(owner_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Store)
    if owner_id:
        q = q.filter(Store.owner_id == owner_id)
    rows = q.order_by(Store.created_at.desc()).all()
    return [{
        "id": str(r.id),
        "owner_id": str(r.owner_id),
        "store_name": r.store_name,
        "store_type": r.store_type,
        "description": r.description,
        "is_open": bool(r.is_open),
        "rating": float(r.rating or 0),
        "created_at": str(r.created_at)
    } for r in rows]

@router.post("/stores")
def create_store(payload: StoreCreate, creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    from common.security import decode_token
    data = decode_token(creds.credentials)
    uid = data.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="invalid_token")
    owner = db.query(UserProfile).filter(UserProfile.id == uid).first()
    if not owner:
        raise HTTPException(status_code=404, detail="owner_not_found")
    obj = Store(owner_id=owner.id, store_name=payload.store_name, store_type=payload.store_type, description=payload.description, is_open=payload.is_open)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": str(obj.id)}

class ProductCreate(BaseModel):
    store_id: str
    category_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    discount: Optional[float] = 0
    quantity: int
    unit: Optional[str] = None
    is_veg: Optional[bool] = None
    expiry_date: Optional[str] = None

@router.get("/products")
def list_products(store_id: Optional[str] = None, category_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Product)
    if store_id:
        q = q.filter(Product.store_id == store_id)
    if category_id:
        q = q.filter(Product.category_id == category_id)
    rows = q.order_by(Product.created_at.desc()).all()
    return [{
        "id": str(r.id),
        "store_id": str(r.store_id) if r.store_id else None,
        "category_id": str(r.category_id) if r.category_id else None,
        "name": r.name,
        "description": r.description,
        "price": float(r.price),
        "discount": float(r.discount or 0),
        "quantity": int(r.quantity),
        "unit": r.unit,
        "is_veg": bool(r.is_veg) if r.is_veg is not None else None,
        "expiry_date": str(r.expiry_date) if r.expiry_date else None,
        "is_available": bool(r.is_available),
        "created_at": str(r.created_at)
    } for r in rows]

@router.post("/products")
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.id == payload.store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="store_not_found")
    obj = Product(
        store_id=store.id,
        category_id=payload.category_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        discount=payload.discount or 0,
        quantity=payload.quantity,
        unit=payload.unit,
        is_veg=payload.is_veg,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": str(obj.id)}

class ProductImageCreate(BaseModel):
    product_id: str
    image_url: Optional[str] = None
    image_data: Optional[str] = None
    image_mime_type: Optional[str] = None

@router.post("/product-images")
def create_product_image(payload: ProductImageCreate, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.id == payload.product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="product_not_found")
    obj = ProductImage(product_id=prod.id, image_url=payload.image_url, image_data=payload.image_data, image_mime_type=payload.image_mime_type)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": str(obj.id)}

@router.get("/cart")
def get_cart(creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    from common.security import decode_token
    data = decode_token(creds.credentials)
    uid = data.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="invalid_token")
    cart = db.query(Cart).filter(Cart.user_id == uid).first()
    if not cart:
        cart = Cart(user_id=uid)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    def item_to_dict(ci: CartItem):
        p = db.query(Product).filter(Product.id == ci.product_id).first()
        price = float(p.price) if p else 0.0
        discount = float(p.discount or 0) if p else 0.0
        return {"id": str(ci.id), "product_id": str(ci.product_id), "quantity": ci.quantity, "price": price, "discount": discount}
    return {"id": str(cart.id), "user_id": str(cart.user_id), "items": [item_to_dict(i) for i in items]}

class CartItemAdd(BaseModel):
    product_id: str
    quantity: int

@router.post("/cart/items")
def add_cart_item(payload: CartItemAdd, creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    from common.security import decode_token
    data = decode_token(creds.credentials)
    uid = data.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="invalid_token")
    cart = db.query(Cart).filter(Cart.user_id == uid).first()
    if not cart:
        cart = Cart(user_id=uid)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    existing = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == payload.product_id).first()
    if existing:
        existing.quantity = existing.quantity + payload.quantity
    else:
        db.add(CartItem(cart_id=cart.id, product_id=payload.product_id, quantity=payload.quantity))
    db.commit()
    return {"ok": True}

@router.delete("/cart/items/{item_id}")
def remove_cart_item(item_id: str, creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    from backend.common.security import decode_token
    data = decode_token(creds.credentials)
    uid = data.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="invalid_token")
    cart = db.query(Cart).filter(Cart.user_id == uid).first()
    if not cart:
        raise HTTPException(status_code=404, detail="cart_not_found")
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="item_not_found")
    db.delete(item)
    db.commit()
    return {"ok": True}

class OrderCreate(BaseModel):
    delivery_address: str

@router.post("/orders")
def create_order(payload: OrderCreate, creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    from backend.common.security import decode_token
    data = decode_token(creds.credentials)
    uid = data.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="invalid_token")
    cart = db.query(Cart).filter(Cart.user_id == uid).first()
    if not cart:
        raise HTTPException(status_code=404, detail="cart_not_found")
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    if not items:
        raise HTTPException(status_code=400, detail="cart_empty")
    total = 0.0
    for ci in items:
        p = db.query(Product).filter(Product.id == ci.product_id).first()
        if p:
            price = float(p.price) - float(p.discount or 0)
            total += price * ci.quantity
    order = Order(user_id=uid, total_amount=total, status="PLACED", delivery_address=payload.delivery_address)
    db.add(order)
    db.commit()
    db.refresh(order)
    for ci in items:
        p = db.query(Product).filter(Product.id == ci.product_id).first()
        if p:
            price = float(p.price) - float(p.discount or 0)
            db.add(OrderItem(order_id=order.id, product_id=p.id, quantity=ci.quantity, price=price))
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return {"id": str(order.id), "total_amount": total, "status": order.status}

@router.get("/orders")
def list_orders(creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    from backend.common.security import decode_token
    data = decode_token(creds.credentials)
    uid = data.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="invalid_token")
    rows = db.query(Order).filter(Order.user_id == uid).order_by(Order.created_at.desc()).all()
    return [{"id": str(r.id), "total_amount": float(r.total_amount or 0), "status": r.status, "created_at": str(r.created_at)} for r in rows]

class PaymentCreate(BaseModel):
    order_id: str
    payment_method: str
    payment_status: str
    transaction_id: Optional[str] = None

@router.post("/payments")
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")
    obj = Payment(order_id=order.id, payment_method=payload.payment_method, payment_status=payload.payment_status, transaction_id=payload.transaction_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": str(obj.id)}

class ReviewCreate(BaseModel):
    product_id: str
    rating: int
    comment: Optional[str] = None

@router.post("/reviews")
def create_review(payload: ReviewCreate, creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    from backend.common.security import decode_token
    data = decode_token(creds.credentials)
    uid = data.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="invalid_token")
    prod = db.query(Product).filter(Product.id == payload.product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="product_not_found")
    obj = Review(user_id=uid, product_id=payload.product_id, rating=payload.rating, comment=payload.comment)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    avg_rating = db.query(func.avg(Review.rating)).filter(Review.product_id == payload.product_id).scalar() or 0
    store = db.query(Store).filter(Store.id == prod.store_id).first()
    if store:
        store.rating = avg_rating
        db.commit()
    return {"id": str(obj.id)}

@router.get("/reviews")
def list_reviews(product_id: str, db: Session = Depends(get_db)):
    rows = db.query(Review).filter(Review.product_id == product_id).order_by(Review.created_at.desc()).all()
    return [{"id": str(r.id), "user_id": str(r.user_id), "product_id": str(r.product_id), "rating": r.rating, "comment": r.comment, "created_at": str(r.created_at)} for r in rows]
