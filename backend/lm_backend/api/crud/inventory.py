"""CRUD operations for inventories."""
from typing import List, Optional

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.schemas.inventory import InventoryCreateSchema, InventoryUpdateSchema, InventorySchema
from lm_backend.models.inventory import Inventory

from fastapi import HTTPException


class InventoryCRUD:
    """
    CRUD operations for inventories.
    """

    async def create(self, db_session: AsyncSession, inventory: InventoryCreateSchema) -> InventorySchema:
        """
        Add a new inventory to the database.
        Returns the newly created inventory.
        """
        new_inventory = Inventory(**inventory.dict())
        try:
            await db_session.add(new_inventory)
            await db_session.commit()
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="Inventory could not be created")
        return InventorySchema.from_orm(new_inventory)

    async def read(self, db_session: AsyncSession, inventory_id: int) -> Optional[InventorySchema]:
        """
        Read a inventory with the given id.
        Returns the inventory.
        """
        query = await db_session.execute(select(Inventory).filter(Inventory.id == inventory_id))
        db_inventory = query.scalars().one_or_none()

        if db_inventory is None:
            raise HTTPException(status_code=404, detail="Inventory not found")

        return InventorySchema.from_orm(db_inventory.scalar_one_or_none())

    async def read_all(self, db_session: AsyncSession) -> List[InventorySchema]:
        """
        Read all inventories.
        Returns a list of inventories.
        """
        query = await db_session.execute(select(Inventory))
        db_inventories = query.scalars().all()
        return [InventorySchema.from_orm(db_inventory) for db_inventory in db_inventories]

    async def update(
        self, db_session: AsyncSession, inventory_id: int, inventory_update: InventoryUpdateSchema
    ) -> Optional[InventorySchema]:
        """
        Update a inventory in the database.
        Returns the updated inventory.
        """
        query = await db_session.execute(select(Inventory).filter(Inventory.id == inventory_id))
        db_inventory = query.scalar_one_or_none()

        if db_inventory is None:
            raise HTTPException(status_code=404, detail="Inventory not found")

        for field, value in inventory_update:
            setattr(db_inventory, field, value)

        await db_session.commit()
        await db_session.refresh(db_inventory)
        return InventorySchema.from_orm(db_inventory)

    async def delete(self, db_session: AsyncSession, inventory_id: int) -> bool:
        """
        Delete a inventory from the database.
        """
        query = await db_session.execute(select(Inventory).filter(Inventory.id == inventory_id))
        db_inventory = query.scalars().one_or_none()

        if db_inventory is None:
            raise HTTPException(status_code=404, detail="Inventory not found")
        try:
            db_session.delete(db_inventory)
            await db_session.flush()
        except Exception:
            raise HTTPException(status_code=400, detail="Inventory could not be deleted")
