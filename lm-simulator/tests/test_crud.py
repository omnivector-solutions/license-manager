import pytest
from fastapi import HTTPException, status
from pytest import mark

from lm_simulator.crud import (
    add_license,
    add_license_in_use,
    list_licenses,
    list_licenses_in_use,
    remove_license,
    remove_license_in_use,
)
from lm_simulator.models import License, LicenseInUse
from lm_simulator.schemas import LicenseRow


@mark.asyncio
async def test__add_license__success(one_license, read_objects, synth_session):
    created_license = await add_license(synth_session, one_license)

    assert created_license.name == one_license.name
    assert created_license.total == one_license.total

    licenses_in_db = await read_objects(License)

    assert len(licenses_in_db) == 1

    assert licenses_in_db[0].name == created_license.name
    assert licenses_in_db[0].total == created_license.total


@mark.asyncio
async def test__add_license__fail_with_duplicate(one_license, synth_session):
    with pytest.raises(HTTPException) as exc_info:
        await add_license(synth_session, one_license)

    assert exc_info.type == HTTPException
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Can't create License, check the input data"


@mark.asyncio
async def test__list_licenses__empty(synth_session):
    licenses = await list_licenses(synth_session)
    assert len(licenses) == 0


@mark.asyncio
async def test__list_licenses__success(licenses, insert_objects, synth_session):
    await insert_objects(licenses, License)

    licenses_in_db = await list_licenses(synth_session)

    assert len(licenses_in_db) == 2

    assert licenses_in_db[0].name == licenses.name
    assert licenses_in_db[0].total == licenses.total

    assert licenses_in_db[1].name == licenses.name
    assert licenses_in_db[1].total == licenses.total


@mark.asyncio
async def test__remove_license__success(one_license, insert_objects, read_objects, synth_session):
    await insert_objects([one_license], License)

    licenses_in_db = await read_objects(License)
    assert len(licenses_in_db) == 1

    await remove_license(synth_session, one_license.name)

    licenses_in_db_after_delete = await read_objects(License)
    assert len(licenses_in_db_after_delete) == 0


@mark.asyncio
async def test__remove_license__fail_with_not_found(one_license, insert_objects, synth_session):
    await insert_objects([one_license], License)

    with pytest.raises(HTTPException) as exc_info:
        await remove_license(synth_session, "non-existing-license")

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "License not found"


@mark.asyncio
async def test__add_license_in_use__success(
    one_license, one_license_in_use, insert_objects, read_objects, synth_session
):
    await insert_objects([one_license], License)

    await add_license_in_use(synth_session, one_license_in_use)

    licenses_in_use_in_db = await read_objects(LicenseInUse)
    assert len(licenses_in_use_in_db) == 1

    assert licenses_in_use_in_db[0].id
    assert licenses_in_use_in_db[0].quantity == one_license_in_use.quantity
    assert licenses_in_use_in_db[0].user_name == one_license_in_use.user_name
    assert licenses_in_use_in_db[0].lead_host == one_license_in_use.lead_host
    assert licenses_in_use_in_db[0].license_name == one_license_in_use.license_name


@mark.asyncio
async def test__add_license_in_use__fail_with_not_enough_licenses(
    one_license, one_license_in_use__not_enough, insert_objects, synth_session
):
    await insert_objects([one_license], License)
    await insert_objects([one_license_in_use__not_enough], LicenseInUse)

    with pytest.raises(HTTPException) as exc_info:
        await add_license_in_use(synth_session, one_license_in_use__not_enough)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Not enough licenses"


@mark.asyncio
async def test__add_license_in_use__fail_with_license_not_found(
    one_license, one_license_in_use__not_found, insert_objects, synth_session
):
    await insert_objects([one_license], LicenseInUse)

    with pytest.raises(HTTPException) as exc_info:
        await add_license_in_use(synth_session, one_license_in_use__not_found)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "License not found"


@mark.asyncio
async def test__list_licenses_in_use__empty(synth_session):
    licenses_in_use = await list_licenses_in_use(synth_session)
    assert len(licenses_in_use) == 0


@mark.asyncio
async def test__list_licenses_in_use__success(licenses, licenses_in_use, insert_objects, synth_session):
    await insert_objects(licenses, License)
    await insert_objects(licenses_in_use, LicenseInUse)

    licenses_in_use_in_db = await list_licenses_in_use(synth_session)

    assert len(licenses_in_use_in_db) == 2

    assert licenses_in_use_in_db[0].id == 1
    assert licenses_in_use_in_db[0].quantity == licenses_in_use[0].quantity
    assert licenses_in_use_in_db[0].user_name == licenses_in_use[0].user_name
    assert licenses_in_use_in_db[0].lead_host == licenses_in_use[0].lead_host
    assert licenses_in_use_in_db[0].license_name == licenses_in_use[0].license_name

    assert licenses_in_use_in_db[1].id == 2
    assert licenses_in_use_in_db[1].quantity == licenses_in_use[1].quantity
    assert licenses_in_use_in_db[1].user_name == licenses_in_use[1].user_name
    assert licenses_in_use_in_db[1].lead_host == licenses_in_use[1].lead_host
    assert licenses_in_use_in_db[1].license_name == licenses_in_use[1].license_name


@mark.asyncio
async def test__remove_license_in_use__success(
    one_license, one_license_in_use, insert_objects, read_objects, synth_session
):
    await insert_objects([one_license], License)
    await insert_objects([one_license_in_use], LicenseInUse)

    licenses_in_use_in_db = await read_objects(LicenseInUse)
    assert len(licenses_in_use_in_db) == 1

    await remove_license_in_use(synth_session, licenses_in_use_in_db[0].id)

    licenses_in_use_in_db_after_delete = await read_objects(LicenseInUse)
    assert len(licenses_in_use_in_db_after_delete) == 0


@mark.asyncio
async def test__remove_license_in_use__fail_with_not_found(
    one_license, one_license_in_use, insert_objects, synth_session
):
    await insert_objects([one_license], License)
    await insert_objects([one_license_in_use], LicenseInUse)

    with pytest.raises(HTTPException) as exc_info:
        await remove_license_in_use(synth_session, 2)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "License In Use not found"


@mark.asyncio
async def test__add_license_in_use__correctly_updates_license_in_use(
    one_license, one_license_in_use, insert_objects, read_objects, synth_session
):
    await insert_objects([one_license], License)

    licenses_in_db = await read_objects(License)
    assert len(licenses_in_db) == 1
    assert LicenseRow.model_validate(licenses_in_db[0]).in_use == 0

    await add_license_in_use(synth_session, one_license_in_use)

    licenses_in_use_in_db = await read_objects(LicenseInUse)
    assert len(licenses_in_use_in_db) == 1
    assert LicenseRow.model_validate(licenses_in_db[0]).in_use == one_license_in_use.quantity


@mark.asyncio
async def test__remove_license_in_use__correctly_updates_license_in_use(
    one_license, one_license_in_use, insert_objects, read_objects, synth_session
):
    await insert_objects([one_license], License)
    await insert_objects([one_license_in_use], LicenseInUse)

    licenses_in_db = await read_objects(License)
    assert len(licenses_in_db) == 1
    assert LicenseRow.model_validate(licenses_in_db[0]).in_use == one_license_in_use.quantity

    remove_license_in_use(synth_session, 1)

    licenses_in_db_after_delete = await read_objects(License)
    assert len(licenses_in_db_after_delete) == 1
    assert LicenseRow.model_validate(licenses_in_db_after_delete[0]).in_use == 0
