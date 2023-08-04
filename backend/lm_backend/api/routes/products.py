from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.product import Product
from lm_backend.api.schemas.product import ProductCreateSchema, ProductSchema, ProductUpdateSchema
from lm_backend.database import SecureSession, secure_session
from lm_backend.permissions import Permissions

router = APIRouter()


crud_product = GenericCRUD(Product, ProductCreateSchema, ProductUpdateSchema)


@router.post(
    "",
    response_model=ProductSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    product: ProductCreateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.PRODUCT_EDIT)),
):
    """Create a new product."""
    return await crud_product.create(db_session=secure_session.session, obj=product)


@router.get(
    "",
    response_model=List[ProductSchema],
    status_code=status.HTTP_200_OK,
)
async def read_all_products(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    secure_session: SecureSession = Depends(secure_session(Permissions.PRODUCT_VIEW)),
):
    """Return all products with associated features."""
    return await crud_product.read_all(
        db_session=secure_session.session, search=search, sort_field=sort_field, sort_ascending=sort_ascending
    )


@router.get(
    "/{product_id}",
    response_model=ProductSchema,
    status_code=status.HTTP_200_OK,
)
async def read_product(
    product_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.PRODUCT_VIEW)),
):
    """Return a product with associated features with the given id."""
    return await crud_product.read(db_session=secure_session.session, id=product_id)


@router.put(
    "/{product_id}",
    response_model=ProductSchema,
    status_code=status.HTTP_200_OK,
)
async def update_product(
    product_id: int,
    product_update: ProductUpdateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.PRODUCT_EDIT)),
):
    """Update a product in the database."""
    return await crud_product.update(
        db_session=secure_session.session,
        id=product_id,
        obj=product_update,
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_product(
    product_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.PRODUCT_EDIT)),
):
    """Delete a product from the database and associated features."""
    return await crud_product.delete(db_session=secure_session.session, id=product_id)
