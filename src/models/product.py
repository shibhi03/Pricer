from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    search_query = Column(String, index=True)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, index=True, nullable=False)
    platform = Column(String, index=True, nullable=False)
    image_url = Column(String)
    rating = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to historical prices
    prices = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="prices")
