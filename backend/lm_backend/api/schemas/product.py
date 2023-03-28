"""
Schemas for products.
"""
from pydantic import BaseModel


class ProductCreateSchema(BaseModel):
    """
    Represents a feature's product.
    """

    name: str


class ProductUpdateSchema(BaseModel):
    name: str


class Product(BaseModel):
    """
    Represents a feature's product.
    """

    id: int
    name: str

    class Config:
        orm_mode = True
