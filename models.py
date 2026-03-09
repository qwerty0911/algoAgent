from sqlalchemy import Column, String, DateTime
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)