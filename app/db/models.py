"""
Database Models and Connection
"""
from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class TransactionModel(Base):
    """Transaction record in database."""
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    device_id = Column(String)
    ip_address = Column(String)
    merchant_id = Column(String)
    transaction_amount = Column(Float)
    risk_score = Column(Float)
    propagation_depth = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
