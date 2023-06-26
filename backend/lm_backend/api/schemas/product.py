"""Product schemas for the License Manager API."""
from typing import Optional

from pydantic import BaseModel

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema


class ProductCreateSchema(BaseCreateSchema):
    """
    Represents a feature's product.
    """

    name: str


class ProductUpdateSchema(BaseUpdateSchema):
    """
    Represents a feature's product.
    """

    name: Optional[str] = None


class ProductSchema(BaseModel):
    """
    Represents a feature's product.
    """

    id: int
    name: str

    class Config:
        orm_mode = True
