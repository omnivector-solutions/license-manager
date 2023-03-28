from lm_backend.api.crud.license_server import LicenseServerCRUD
from lm_backend.api.schemas.license_server import LicenseServerCreateSchema
from lm_backend.database import get_session


async def test():
    session = get_session()
    update = LicenseServerCreateSchema(port=123)
    CRUD = LicenseServerCRUD()
    await CRUD.update(db_session=session, license_server_update=update)


test()
