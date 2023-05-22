from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.product import Product
from lm_backend.api.schemas.product import ProductCreateSchema, ProductSchema, ProductUpdateSchema
from lm_backend.permissions import Permissions
from lm_backend.security import guard
from lm_backend.session import get_session

router = APIRouter()


crud_product = GenericCRUD(Product, ProductCreateSchema, ProductUpdateSchema)


@router.post(
    "/",
    response_model=ProductSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(guard.lockdown(Permissions.PRODUCT_EDIT))],
)
async def create_product(
    product: ProductCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new product."""
    return await crud_product.create(db_session=db_session, obj=product)


@router.get(
    "/",
    response_model=List[ProductSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.PRODUCT_VIEW))],
)
async def read_all_products(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    db_session: AsyncSession = Depends(get_session),
):
    """Return all products with associated features."""
    return await crud_product.read_all(
        db_session=db_session, search=search, sort_field=sort_field, sort_ascending=sort_ascending
    )


@router.get(
    "/{product_id}",
    response_model=ProductSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.PRODUCT_VIEW))],
)
async def read_product(product_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a product with associated features with the given id."""
    return await crud_product.read(db_session=db_session, id=product_id)


@router.put(
    "/{product_id}",
    response_model=ProductSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.PRODUCT_EDIT))],
)
async def update_product(
    product_id: int,
    product_update: ProductUpdateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Update a product in the database."""
    return await crud_product.update(
        db_session=db_session,
        id=product_id,
        obj=product_update,
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.PRODUCT_EDIT))],
)
async def delete_product(product_id: int, db_session: AsyncSession = Depends(get_session)):
    """Delete a product from the database and associated features."""
    return await crud_product.delete(db_session=db_session, id=product_id)
