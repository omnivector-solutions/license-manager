"""CRUD operations for products."""
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from lm_backend.api.schemas.product import ProductCreateSchema, ProductSchema, ProductUpdateSchema
from lm_backend.models.product import Product


class ProductCRUD:
    """
    CRUD operations for products.
    """

    async def create(self, db_session: AsyncSession, product: ProductCreateSchema) -> ProductSchema:
        """
        Add a new product to the database.
        Returns the newly created product.
        """
        new_product = Product(**product.dict())
        try:
            await db_session.add(new_product)
            await db_session.commit()
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="Product could not be created")
        return ProductSchema.from_orm(new_product)

    async def read(self, db_session: AsyncSession, product_id: int) -> Optional[ProductSchema]:
        """
        Read a product with the given id.
        Returns the product.
        """
        query = await db_session.execute(select(Product).filter(Product.id == product_id))
        db_product = query.scalars().one_or_none()

        if db_product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        return ProductSchema.from_orm(db_product.scalar_one_or_none())

    async def read_all(self, db_session: AsyncSession) -> List[ProductSchema]:
        """
        Read all products.
        Returns a list of products.
        """
        query = await db_session.execute(select(Product))
        db_products = query.scalars().all()
        return [ProductSchema.from_orm(db_product) for db_product in db_products]

    async def update(
        self, db_session: AsyncSession, product_id: int, product_update: ProductUpdateSchema
    ) -> Optional[ProductSchema]:
        """
        Update a product in the database.
        Returns the updated product.
        """
        query = await db_session.execute(select(Product).filter(Product.id == product_id))
        db_product = query.scalar_one_or_none()

        if db_product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        for field, value in product_update:
            setattr(db_product, field, value)

        await db_session.commit()
        await db_session.refresh(db_product)
        return ProductSchema.from_orm(db_product)

    async def delete(self, db_session: AsyncSession, product_id: int) -> bool:
        """
        Delete a product from the database.
        """
        query = await db_session.execute(select(Product).filter(Product.id == product_id))
        db_product = query.scalars().one_or_none()

        if db_product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        try:
            db_session.delete(db_product)
            await db_session.flush()
        except Exception:
            raise HTTPException(status_code=400, detail="Product could not be deleted")
