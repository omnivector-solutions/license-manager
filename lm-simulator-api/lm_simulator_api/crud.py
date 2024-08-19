from typing import List

from buzz import enforce_defined, handle_errors, require_condition
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from lm_simulator_api.constants import LicenseServerType
from lm_simulator_api.models import License, LicenseInUse
from lm_simulator_api.schemas import LicenseCreate, LicenseInUseCreate, LicenseInUseRow, LicenseRow


async def add_license(session: Session, license: LicenseCreate) -> LicenseRow:
    """
    Add a new License to the database.
    """
    query = await session.execute(select(License).where(License.name == license.name))
    require_condition(
        query.scalar_one_or_none() is None,
        "License already exists",
        raise_exc_class=HTTPException,
        exc_builder=lambda exc_class, msg: exc_class(
            status_code=status.HTTP_409_CONFLICT,
            detail="License already exists",
        ),
    )

    db_license = License(**license.model_dump())

    with handle_errors(
        "Can't create License",
        raise_exc_class=HTTPException,
        exc_builder=lambda exc_class, msg: exc_class(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed, check the input data",
        ),
    ):
        session.add(db_license)
        await session.flush()
        await session.refresh(db_license)

        return LicenseRow.model_validate(db_license, from_attributes=True)


async def list_licenses(session: Session) -> List[LicenseRow]:
    """
    List all Licenses in the database.
    """
    query = await session.execute(select(License))
    db_licenses = query.scalars().all()
    return [LicenseRow.model_validate(license) for license in db_licenses]


async def list_licenses_by_server_type(session: Session, server_type: LicenseServerType) -> List[LicenseRow]:
    """
    List all Licenses in the database by server type.
    """
    query = await session.execute(select(License).where(License.license_server_type == server_type))
    db_licenses = query.scalars().all()
    return [LicenseRow.model_validate(license) for license in db_licenses]


async def read_license_by_name(session: Session, license_name: str) -> LicenseRow:
    """
    Retrive the License in the database by name.
    """
    query = await session.execute(select(License).where(License.name == license_name))
    db_license = enforce_defined(
        query.scalar_one_or_none(),
        "License not found",
        raise_exc_class=HTTPException,
        exc_builder=lambda exc_class, msg: exc_class(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        ),
    )

    return LicenseRow.model_validate(db_license)


async def remove_license(session: Session, license_name: str):
    """
    Remove the License from the database.

    Raises LicenseNotFound if the License does not exist.
    """
    query = await session.execute(select(License).where(License.name == license_name))
    db_license = enforce_defined(
        query.scalar_one_or_none(),
        "License not found",
        raise_exc_class=HTTPException,
        exc_builder=lambda exc_class, msg: exc_class(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        ),
    )

    with handle_errors(
        "Can't remove License",
        raise_exc_class=HTTPException,
        exc_builder=lambda exc_class, msg: exc_class(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed, check the input data",
        ),
    ):
        await session.delete(db_license)
        await session.flush()


async def add_license_in_use(session: Session, license_in_use: LicenseInUseCreate) -> LicenseInUseRow:
    """
    Add a new LicenseInUse to the database.
    """
    query = await session.execute(select(License).where(License.name == license_in_use.license_name))
    db_license = enforce_defined(
        query.scalar_one_or_none(),
        "License not found",
        raise_exc_class=HTTPException,
        exc_builder=lambda exc_class, msg: exc_class(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        ),
    )
    license_row = LicenseRow.model_validate(db_license)

    require_condition(
        license_row.total >= license_in_use.quantity + license_row.in_use,
        "Not enough licenses",
        raise_exc_class=HTTPException,
        exc_builder=lambda exc_class, msg: exc_class(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough licenses",
        ),
    )

    db_license_in_use = LicenseInUse(**license_in_use.model_dump())

    with handle_errors(
        "Can't create License In Use",
        raise_exc_class=HTTPException,
        exc_builder=lambda exc_class, msg: exc_class(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Can't create License In Use, check the input data",
        ),
    ):
        session.add(db_license_in_use)
        await session.flush()
        await session.refresh(db_license_in_use)

        return LicenseInUseRow.model_validate(db_license_in_use)


async def list_licenses_in_use(session: Session) -> List[LicenseInUseRow]:
    """
    List all LicensesInUse in the database.
    """
    query = await session.execute(select(LicenseInUse))
    db_licenses_in_use = query.scalars().all()
    return [LicenseInUseRow.model_validate(license_in_use) for license_in_use in db_licenses_in_use]


async def remove_license_in_use(
    session: Session,
    id: int,
):
    """
    Remove the LicenseInUse from the database.

    Raises LicenseNotFound if the LicenseInUse does not exist.
    """
    query = await session.execute(select(LicenseInUse).where(LicenseInUse.id == id))
    db_license_in_use = enforce_defined(
        query.scalars().one_or_none(),
        "License In Use not found",
        raise_exc_class=HTTPException,
        exc_builder=lambda exc_class, msg: exc_class(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License In Use not found",
        ),
    )

    with handle_errors(
        "Can't remove License In Use",
        raise_exc_class=HTTPException,
        exc_builder=lambda exc_class, msg: exc_class(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed, check the input data",
        ),
    ):
        await session.delete(db_license_in_use)
        await session.flush()
