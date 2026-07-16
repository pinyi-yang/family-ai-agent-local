from sqlalchemy import Column, String, Integer, Boolean, Text
from .database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    google_refresh_token = Column(String, nullable=True)
    is_authenticated = Column(Boolean, default=False)

class FamilyPreferences(Base):
    __tablename__ = "family_preferences"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String)
    sub_type = Column(String)
    lead_time_days = Column(Integer)
    preferred_season = Column(String, nullable=True)
    preferences_summary = Column(Text, nullable=True)
