from lm_backend.api.license_server.crud import LicenseServerCRUD
from lm_backend.database.storage import async_session


async def get_license_server_crud() -> LicenseServerCRUD:
    async with async_session() as session:
        async with session.begin():
            yield LicenseServerCRUD(async_session=session)
