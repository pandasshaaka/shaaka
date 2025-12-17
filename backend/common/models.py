from sqlalchemy import Column, String, Text, TIMESTAMP, Numeric, Integer, Boolean, Date, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from .db import Base
import base64


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    full_name = Column(String(255), nullable=False)
    mobile_no = Column(String(20), nullable=False, unique=True)
    password = Column(Text, nullable=False)
    gender = Column(String(20))
    category = Column(String(50), nullable=False)
    address_line = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    pincode = Column(String(20))
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    profile_photo_url = Column(Text)
    profile_photo_data = Column(Text)  # Base64 encoded image data
    profile_photo_mime_type = Column(String(50))  # e.g., 'image/jpeg', 'image/png'
    created_at = Column(TIMESTAMP, server_default=text("NOW()"))
    updated_at = Column(TIMESTAMP, server_default=text("NOW()"))

    def set_profile_photo(self, image_data: bytes, mime_type: str):
        """Store profile photo as base64 in database"""
        self.profile_photo_data = base64.b64encode(image_data).decode('utf-8')
        self.profile_photo_mime_type = mime_type
        self.profile_photo_url = f"data:{mime_type};base64,{self.profile_photo_data}"

    def get_profile_photo_data(self) -> bytes:
        """Get profile photo data as bytes"""
        if self.profile_photo_data:
            return base64.b64decode(self.profile_photo_data)
        return None


class Store(Base):
    __tablename__ = "stores"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    store_name = Column(String(255), nullable=False)
    store_type = Column(String(50))
    description = Column(Text)
    is_open = Column(Boolean, server_default=text("TRUE"))
    rating = Column(Numeric(2, 1), server_default=text("0"))
    created_at = Column(TIMESTAMP, server_default=text("NOW()"))


class Category(Base):
    __tablename__ = "categories"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String(100), nullable=False, unique=True)


class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"))
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(5, 2), server_default=text("0"))
    quantity = Column(Integer, nullable=False)
    unit = Column(String(50))
    is_veg = Column(Boolean)
    expiry_date = Column(Date)
    is_available = Column(Boolean, server_default=text("TRUE"))
    created_at = Column(TIMESTAMP, server_default=text("NOW()"))


class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"))
    image_url = Column(Text)
    image_data = Column(Text)
    image_mime_type = Column(String(50))


class Cart(Base):
    __tablename__ = "carts"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"))
    updated_at = Column(TIMESTAMP, server_default=text("NOW()"))


class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)


class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
    total_amount = Column(Numeric(10, 2))
    status = Column(String(50))
    delivery_address = Column(Text)
    created_at = Column(TIMESTAMP, server_default=text("NOW()"))


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Numeric(10, 2))


class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    payment_method = Column(String(50))
    payment_status = Column(String(50))
    transaction_id = Column(Text)
    paid_at = Column(TIMESTAMP)


class Donation(Base):
    __tablename__ = "donations"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    donor_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
    food_name = Column(String(255))
    quantity = Column(Integer)
    description = Column(Text)
    pickup_address = Column(Text)
    status = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=text("NOW()"))


class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    vehicle_type = Column(String(50))
    license_number = Column(String(100))
    is_available = Column(Boolean, server_default=text("TRUE"))


class DeliveryAssignment(Base):
    __tablename__ = "delivery_assignments"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    delivery_partner_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    donation_id = Column(UUID(as_uuid=True), ForeignKey("donations.id"))
    status = Column(String(50))
    assigned_at = Column(TIMESTAMP, server_default=text("NOW()"))


class Review(Base):
    __tablename__ = "reviews"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(TIMESTAMP, server_default=text("NOW()"))


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
    title = Column(String(255))
    message = Column(Text)
    is_read = Column(Boolean, server_default=text("FALSE"))
    created_at = Column(TIMESTAMP, server_default=text("NOW()"))
