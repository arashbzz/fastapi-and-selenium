from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DATE
from .database import Base


class Products(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    id_product = Column(Integer, unique=False)

    price = relationship("Price", back_populates="product")


class Price(Base):
    __tablename__ = "price"

    id = Column(Integer, primary_key=True, index=True)
    price = Column(Float(precision=2))
    date = Column(DATE)
    id_product = Column(Integer, ForeignKey("products.id"))

    product = relationship("Products", back_populates="price")
