"""Product schemas for the License Manager API."""
from typing import Optional

from pydantic import ConfigDict, BaseModel, Field

from lm_api.api.schemas.base import BaseCreateSchema, BaseUpdateSchema


class ProductCreateSchema(BaseCreateSchema):
    """
    Represents a feature's product.
    """

    name: str = Field(
        ..., title="Name of the product", max_length=255, description="The name of the product."
    )


class ProductUpdateSchema(BaseUpdateSchema):
    """
    Represents a feature's product.
    """

    name: Optional[str] = Field(
        None, title="Name of the product", max_length=255, description="The name of the product."
    )


class ProductSchema(BaseModel):
    """
    Represents a feature's product.
    """

    id: int = Field(..., title="ID", description="The ID of the product.")
    name: str = Field(
        ..., title="Name of the product", max_length=255, description="The name of the product."
    )
    model_config = ConfigDict(from_attributes=True)
