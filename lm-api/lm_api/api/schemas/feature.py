"""Feature schemas for the License Manager API."""
from typing import Optional

from pydantic import ConfigDict, BaseModel, Field, NonNegativeInt

from lm_api.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from lm_api.api.schemas.product import ProductSchema


class FeatureCreateSchema(BaseCreateSchema):
    """
    Represents the features in a feature configuration.
    """

    name: str = Field(
        ..., title="Name of the feature", max_length=255, description="The name of the feature."
    )
    product_id: int = Field(..., title="Product ID", description="The ID of the product of the feature.")
    config_id: int = Field(
        ..., title="Configuration ID", description="The ID of the configuration that the feature belongs to."
    )
    reserved: int = Field(
        0,
        ge=0,
        le=2**31 - 1,
        title="Reserved quantity",
        description="The quantity of the feature that is reserved for usage in desktop environments.",
    )


class FeatureWithoutConfigIdCreateSchema(BaseCreateSchema):
    """
    Represents the features in a feature configuration.
    """

    name: str = Field(
        ..., title="Name of the feature", max_length=255, description="The name of the feature."
    )
    product_id: int = Field(..., title="Product ID", description="The ID of the product of the feature.")
    reserved: int = Field(
        0,
        ge=0,
        le=2**31 - 1,
        title="Reserved quantity",
        description="The quantity of the feature that is reserved for usage in desktop environments.",
    )


class FeatureWithOptionalIdUpdateSchema(BaseUpdateSchema):
    """
    Feature to be updated in the database.
    """

    id: Optional[int] = Field(None, title="ID", description="The ID of the feature.")
    name: Optional[str] = Field(
        None, title="Name of the feature", max_length=255, description="The name of the feature."
    )
    product_id: Optional[int] = Field(
        None, title="Product ID", description="The ID of the product of the feature."
    )
    reserved: Optional[int] = Field(
        None,
        ge=0,
        le=2**31 - 1,
        title="Reserved quantity",
        description="The quantity of the feature that is reserved for usage in desktop environments.",
    )


class FeatureUpdateSchema(BaseUpdateSchema):
    """
    Represents the features in a feature configuration.
    """

    name: Optional[str] = Field(
        None, title="Name of the feature", max_length=255, description="The name of the feature."
    )
    product_id: Optional[int] = Field(
        None, title="Product ID", description="The ID of the product of the feature."
    )
    config_id: Optional[int] = Field(
        None, title="Configuration ID", description="The ID of the configuration that the feature belongs to."
    )
    reserved: Optional[int] = Field(
        None,
        ge=0,
        le=2**31 - 1,
        title="Reserved quantity",
        description="The quantity of the feature that is reserved for usage in desktop environments.",
    )
    total: Optional[int] = Field(
        None,
        ge=0,
        le=2**31 - 1,
        title="Total quantity",
        description="The total quantity of licenses.",
    )
    used: Optional[int] = Field(
        None,
        ge=0,
        le=2**31 - 1,
        title="Used quantity",
        description="The quantity of the feature that is used.",
    )


class FeatureUpdateByNameSchema(BaseUpdateSchema):
    """
    Represents the feature usage data that will be updated using the
    product and feature name as a filter.
    """

    product_name: str = Field(
        ..., title="Product name", max_length=255, description="The name of the product."
    )
    feature_name: str = Field(
        ..., title="Feature name", max_length=255, description="The name of the feature."
    )
    total: int = Field(
        0,
        ge=0,
        le=2**31 - 1,
        title="Total quantity",
        description="The total quantity of licenses.",
    )
    used: int = Field(
        0,
        ge=0,
        le=2**31 - 1,
        title="Used quantity",
        description="The quantity of the feature that is used.",
    )


class FeatureSchema(BaseModel):
    """
    Represents the features in a feature configuration.
    """

    id: int = Field(..., title="ID", description="The ID of the feature.")
    name: str = Field(
        ..., title="Name of the feature", max_length=255, description="The name of the feature."
    )
    product: ProductSchema = Field(
        ..., title="Product of the feature", description="The product of the feature."
    )
    config_id: int = Field(
        ..., title="Configuration ID", description="The ID of the configuration that the feature belongs to."
    )
    reserved: NonNegativeInt = Field(
        0,
        title="Reserved quantity",
        description="The quantity of the feature that is reserved for usage in desktop environments.",
    )
    total: NonNegativeInt = Field(
        0,
        title="Total quantity",
        description="The total quantity of licenses.",
    )
    used: NonNegativeInt = Field(
        0,
        title="Used quantity",
        description="The quantity of the feature that is used.",
    )
    booked_total: Optional[NonNegativeInt] = Field(
        0,
        title="Booked total quantity",
        description="The total quantity of licenses that are booked.",
    )
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_flat_dict(cls, d):
        return cls(
            product=ProductSchema(
                id=d["product_id"],
                name=d["product_name"],
            ),
            **{k: v for (k, v) in d.items() if not k.startswith("product")},
        )
