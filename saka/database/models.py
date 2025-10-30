from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False)
    asset = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False)
    executed_price = Column(Float, nullable=False)
    executed_quantity = Column(Float, nullable=False)
    amount_usd = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    raw_response = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Trade(id={self.id}, order_id='{self.order_id}', asset='{self.asset}')>"