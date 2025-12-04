from sqlalchemy import Column, String, Text, TIMESTAMP, Numeric, text
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
