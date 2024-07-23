from typing import List

from buzz import enforce_defined, handle_errors, require_condition
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from lm_simulator.models import License, LicenseInUse
from lm_simulator.schemas import LicenseCreate, LicenseInUseCreate, LicenseInUseRow, LicenseRow


async def add_license(session: Session, license: LicenseCreate) -> LicenseRow:
    """
    Add a new License to the database.
    """
    db_license = License(**license.model_dump())

    with handle_errors(
        "Can't create License, check the input data",
        raise_exc_class=HTTPException,
        exc_builder=lambda exc_class, msg: exc_class(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can't create License, check the input data",
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


async def remove_license(session: Session, license_name: str):
    """
    Remove the License from the database.

    Raises LicenseNotFound if the License does not exist.
    """
    query = await session.execute(select(License).where(License.name == license_name))
    db_license = query.scalar_one_or_none()
    enforce_defined(
        db_license,
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
            status_code=status.HTTP_400_BAD_REQUEST,
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
    db_license = query.scalar_one_or_none()
    enforce_defined(
        db_license,
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
            status_code=status.HTTP_400_BAD_REQUEST,
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
    db_license_in_use = query.scalars().one_or_none()

    enforce_defined(
        db_license_in_use,
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database operation failed, check the input data",
        ),
    ):
        await session.delete(db_license_in_use)
        await session.flush()
