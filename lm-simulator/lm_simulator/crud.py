from typing import List

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from lm_simulator.models import License, LicenseInUse
from lm_simulator.schemas import LicenseCreate, LicenseInUseCreate, LicenseInUseRow, LicenseRow


class LicenseNotFound(Exception):
    """The requested license is not found."""


class NotEnoughLicenses(Exception):
    """The number of requested licenses is bigger than the available."""


def get_licenses(session: Session) -> List[LicenseRow]:
    db_licenses = session.execute(select(License)).scalars().all()
    return [LicenseRow.from_orm(license) for license in db_licenses]


def get_licenses_in_use(session: Session) -> List[LicenseInUseRow]:
    db_licenses_in_use = session.execute(select(LicenseInUse)).scalars().all()
    return [LicenseInUseRow.from_orm(license) for license in db_licenses_in_use]


def get_licenses_in_use_from_name(session: Session, license_name: str) -> List[LicenseInUse]:
    db_licenses_in_use = (
        session.execute(select(LicenseInUse).where(LicenseInUse.license_name == license_name)).scalars().all()
    )
    return [LicenseInUseRow.from_orm(license) for license in db_licenses_in_use]


def create_license(session: Session, license: LicenseCreate) -> LicenseRow:
    db_license = License(**license.dict())
    session.add(db_license)
    session.commit()
    session.refresh(db_license)
    return LicenseRow.from_orm(db_license)


def _get_license_available(session: Session, license_name: str) -> LicenseRow:
    license = session.execute(select(License).where(License.name == license_name)).scalars().first()
    return license


def create_license_in_use(session: Session, license_in_use: LicenseInUseCreate) -> LicenseInUseRow:
    """Create the license_in_use.

    We must ensure that there is a license with the license_name in the database, if there is not we raise
    a LicenseNotFound exception.
    Given that the license exists in the database, the total number of licenses must be greater than or equal
    the in_use value for the license plus the quantity needed for the new license_in_use. If it is not, then
    raise a NotEnoughLicenses exception.
    If all the conditions are satisfied, the license_in_use is created and returned.
    """
    license = _get_license_available(session, license_in_use.license_name)
    if not license:
        raise LicenseNotFound()
    license_row = LicenseRow.from_orm(license)
    if license_row.total < license_in_use.quantity + license_row.in_use:
        raise NotEnoughLicenses()
    db_license_in_use = LicenseInUse(**license_in_use.dict())
    session.add(db_license_in_use)
    session.commit()
    session.refresh(db_license_in_use)
    return LicenseInUseRow.from_orm(db_license_in_use)


def _get_licenses_in_database(
    session: Session,
    lead_host: str,
    user_name: str,
    quantity: int,
    license_name: str,
) -> List[LicenseInUse]:
    stmt = (
        select(LicenseInUse)
        .join(License)
        .where(
            License.name == license_name,
            LicenseInUse.lead_host == lead_host,
            LicenseInUse.user_name == user_name,
            LicenseInUse.quantity == quantity,
        )
    )
    licenses = session.execute(stmt).scalars().all()
    return licenses


def delete_license_in_use(
    session: Session,
    lead_host: str,
    user_name: str,
    quantity: int,
    license_name: str,
):
    """Delete the license_in_use from the database.

    To be able to delete a license_in_use, the license_in_use must exists in the database, if it doesn't
    then we raise a LicenseNotFound exception.
    """
    licenses = _get_licenses_in_database(session, lead_host, user_name, quantity, license_name)
    if not licenses:
        raise LicenseNotFound()

    ids_to_delete = [license.id for license in licenses]
    for id in ids_to_delete:
        session.execute(delete(LicenseInUse).where(LicenseInUse.id == id))

    session.commit()


def delete_license(
    session: Session,
    license_name: str,
):
    """Delete the license from the database.

    To be able to delete a license, the license must exists in the database, if it doesn't
    then we raise a LicenseNotFound exception.
    """
    license = _get_license_available(session, license_name)
    if not license:
        raise LicenseNotFound()

    session.execute(delete(License).where(License.name == license_name))
    session.commit()
