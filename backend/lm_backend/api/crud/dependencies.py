from lm_backend.api.crud.generic_crud import GenericCRUD
from lm_backend.database.storage import async_session


async def get_generic_crud() -> GenericCRUD:
    async with async_session() as session:
        async with session.begin():
            yield GenericCRUD(async_session=session)
