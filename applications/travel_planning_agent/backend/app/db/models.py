from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("PlanSession", back_populates="user")


class PlanSession(Base):
    __tablename__ = "plan_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    plans = relationship("TravelPlan", back_populates="session", cascade="all, delete-orphan")


class TravelPlan(Base):
    __tablename__ = "travel_plans"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("plan_sessions.id"), nullable=False)
    request_payload = Column(Text, nullable=False)
    response_payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("PlanSession", back_populates="plans")
