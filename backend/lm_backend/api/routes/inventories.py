from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.inventory import Inventory
from lm_backend.api.schemas.inventory import InventoryCreateSchema, InventorySchema, InventoryUpdateSchema
from lm_backend.permissions import Permissions
from lm_backend.security import guard
from lm_backend.session import get_session

router = APIRouter()


crud_inventory = GenericCRUD(Inventory, InventoryCreateSchema, InventoryUpdateSchema)


@router.post(
    "/",
    response_model=InventorySchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(guard.lockdown(Permissions.INVENTORY_EDIT))],
)
async def create_inventory(
    inventory: InventoryCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new inventory."""
    return await crud_inventory.create(db_session=db_session, obj=inventory)


@router.get(
    "/",
    response_model=List[InventorySchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.INVENTORY_VIEW))],
)
async def read_all_inventories(db_session: AsyncSession = Depends(get_session)):
    """Return all inventories."""
    return await crud_inventory.read_all(db_session=db_session)


@router.get(
    "/{inventory_id}",
    response_model=InventorySchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.INVENTORY_VIEW))],
)
async def read_inventory(inventory_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a inventory for a feature."""
    return await crud_inventory.read(db_session=db_session, id=inventory_id)


@router.put(
    "/{inventory_id}",
    response_model=InventorySchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.INVENTORY_EDIT))],
)
async def update_inventory(
    inventory_id: int,
    inventory_update: InventoryUpdateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Update an inventory in the database."""
    return await crud_inventory.update(
        db_session=db_session,
        id=inventory_id,
        obj=inventory_update,
    )


@router.delete(
    "/{inventory_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.INVENTORY_EDIT))],
)
async def delete_inventory(inventory_id: int, db_session: AsyncSession = Depends(get_session)):
    """Delete an inventory from the database."""
    return await crud_inventory.delete(db_session=db_session, id=inventory_id)
