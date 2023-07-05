from typing import List

from fastapi import APIRouter, Depends, status

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.inventory import Inventory
from lm_backend.api.schemas.inventory import InventoryCreateSchema, InventorySchema, InventoryUpdateSchema
from lm_backend.permissions import Permissions
from lm_backend.database import SecureSession, secure_session

router = APIRouter()


crud_inventory = GenericCRUD(Inventory, InventoryCreateSchema, InventoryUpdateSchema)


@router.post(
    "/",
    response_model=InventorySchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_inventory(
    inventory: InventoryCreateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.INVENTORY_EDIT)),
):
    """Create a new inventory."""
    return await crud_inventory.create(db_session=secure_session.session, obj=inventory)


@router.get(
    "/",
    response_model=List[InventorySchema],
    status_code=status.HTTP_200_OK,
)
async def read_all_inventories(
    secure_session: SecureSession = Depends(secure_session(Permissions.INVENTORY_VIEW)),
):
    """Return all inventories."""
    return await crud_inventory.read_all(db_session=secure_session.session)


@router.get(
    "/{inventory_id}",
    response_model=InventorySchema,
    status_code=status.HTTP_200_OK,
)
async def read_inventory(
    inventory_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.INVENTORY_VIEW)),
):
    """Return a inventory for a feature."""
    return await crud_inventory.read(db_session=secure_session.session, id=inventory_id)


@router.put(
    "/{inventory_id}",
    response_model=InventorySchema,
    status_code=status.HTTP_200_OK,
)
async def update_inventory(
    inventory_id: int,
    inventory_update: InventoryUpdateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.INVENTORY_EDIT)),
):
    """Update an inventory in the database."""
    return await crud_inventory.update(
        db_session=secure_session.session,
        id=inventory_id,
        obj=inventory_update,
    )


@router.delete(
    "/{inventory_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_inventory(
    inventory_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.INVENTORY_EDIT)),
):
    """Delete an inventory from the database."""
    return await crud_inventory.delete(db_session=secure_session.session, id=inventory_id)
