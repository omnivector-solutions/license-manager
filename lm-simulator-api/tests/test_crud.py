from fastapi import HTTPException, status
from lm_simulator_api.crud import (
    add_license,
    add_license_in_use,
    list_licenses,
    list_licenses_in_use,
    read_license_by_name,
    list_licenses_by_server_type,
    remove_license,
    remove_license_in_use,
)
from lm_simulator_api.models import License, LicenseInUse
from lm_simulator_api.schemas import LicenseRow
from pytest import mark, raises


@mark.asyncio
async def test__add_license__success(one_license, read_objects, synth_session):
    created_license = await add_license(synth_session, one_license)

    assert created_license.name == one_license.name
    assert created_license.total == one_license.total

    licenses_in_db = await read_objects(License)

    assert len(licenses_in_db) == 1

    assert licenses_in_db[0].name == created_license.name
    assert licenses_in_db[0].total == created_license.total
    assert licenses_in_db[0].license_server_type == created_license.license_server_type


@mark.asyncio
async def test__add_license__fail_with_duplicate(one_license, synth_session):
    with raises(HTTPException) as exc_info:
        await add_license(synth_session, one_license)
        await add_license(synth_session, one_license)

    assert exc_info.type == HTTPException
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert exc_info.value.detail == "License already exists"


@mark.asyncio
async def test__list_licenses__empty(synth_session):
    licenses = await list_licenses(synth_session)
    assert len(licenses) == 0


@mark.asyncio
async def test__list_licenses__success(licenses, insert_objects, synth_session):
    await insert_objects(licenses, License)

    licenses_in_db = await list_licenses(synth_session)

    assert len(licenses_in_db) == 2

    assert licenses_in_db[0].name == licenses[0].name
    assert licenses_in_db[0].total == licenses[0].total
    assert licenses_in_db[0].license_server_type == licenses[0].license_server_type

    assert licenses_in_db[1].name == licenses[1].name
    assert licenses_in_db[1].total == licenses[1].total
    assert licenses_in_db[1].license_server_type == licenses[1].license_server_type


@mark.asyncio
async def test__read_license_by_name__success(one_license, insert_objects, synth_session):
    await insert_objects([one_license], License)

    license_in_db = await read_license_by_name(synth_session, one_license.name)

    assert license_in_db.name == one_license.name
    assert license_in_db.total == one_license.total
    assert license_in_db.license_server_type == one_license.license_server_type


@mark.asyncio
async def test__read_license_by_name__fail_with_not_found(one_license, insert_objects, synth_session):
    await insert_objects([one_license], License)

    with raises(HTTPException) as exc_info:
        await read_license_by_name(synth_session, "non-existing-license")

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "License not found"


@mark.asyncio
async def test__list_licenses_by_server_type__empty(synth_session):
    licenses = await list_licenses_by_server_type(synth_session, "flexlm")
    assert len(licenses) == 0


@mark.asyncio
async def test__list_licenses_by_server_type__success(licenses, insert_objects, synth_session):
    await insert_objects(licenses, License)

    licenses_in_db = await list_licenses_by_server_type(synth_session, "flexlm")

    assert len(licenses_in_db) == 2

    assert licenses_in_db[0].name == licenses[0].name
    assert licenses_in_db[0].total == licenses[0].total
    assert licenses_in_db[0].license_server_type == licenses[0].license_server_type

    assert licenses_in_db[1].name == licenses[1].name
    assert licenses_in_db[1].total == licenses[1].total
    assert licenses_in_db[1].license_server_type == licenses[1].license_server_type


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

    with raises(HTTPException) as exc_info:
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

    with raises(HTTPException) as exc_info:
        await add_license_in_use(synth_session, one_license_in_use__not_enough)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Not enough licenses"


@mark.asyncio
async def test__add_license_in_use__fail_with_license_not_found(
    one_license, one_license_in_use__not_found, insert_objects, synth_session
):
    await insert_objects([one_license], License)

    with raises(HTTPException) as exc_info:
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
    inserted = await insert_objects(licenses_in_use, LicenseInUse)

    licenses_in_use_in_db = await list_licenses_in_use(synth_session)

    assert len(licenses_in_use_in_db) == 2

    assert licenses_in_use_in_db[0].id == inserted[0].id
    assert licenses_in_use_in_db[0].quantity == inserted[0].quantity
    assert licenses_in_use_in_db[0].user_name == inserted[0].user_name
    assert licenses_in_use_in_db[0].lead_host == inserted[0].lead_host
    assert licenses_in_use_in_db[0].license_name == inserted[0].license_name

    assert licenses_in_use_in_db[1].id == inserted[1].id
    assert licenses_in_use_in_db[1].quantity == inserted[1].quantity
    assert licenses_in_use_in_db[1].user_name == inserted[1].user_name
    assert licenses_in_use_in_db[1].lead_host == inserted[1].lead_host
    assert licenses_in_use_in_db[1].license_name == inserted[1].license_name


@mark.asyncio
async def test__remove_license_in_use__success(
    one_license, one_license_in_use, insert_objects, read_objects, synth_session
):
    await insert_objects([one_license], License)
    inserted = await insert_objects([one_license_in_use], LicenseInUse)

    licenses_in_use_in_db = await read_objects(LicenseInUse)
    assert len(licenses_in_use_in_db) == 1

    await remove_license_in_use(synth_session, inserted[0].id)

    licenses_in_use_in_db_after_delete = await read_objects(LicenseInUse)
    assert len(licenses_in_use_in_db_after_delete) == 0


@mark.asyncio
async def test__remove_license_in_use__fail_with_not_found(
    one_license, one_license_in_use, insert_objects, synth_session
):
    await insert_objects([one_license], License)
    await insert_objects([one_license_in_use], LicenseInUse)

    with raises(HTTPException) as exc_info:
        await remove_license_in_use(synth_session, 0)

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

    licenses_in_db_after_add = await read_objects(License)
    assert len(licenses_in_db_after_add) == 1
    assert LicenseRow.model_validate(licenses_in_db_after_add[0]).in_use == one_license_in_use.quantity


@mark.asyncio
async def test__remove_license_in_use__correctly_updates_license_in_use(
    one_license, one_license_in_use, insert_objects, read_objects, synth_session
):
    await insert_objects([one_license], License)
    inserted = await insert_objects([one_license_in_use], LicenseInUse)

    licenses_in_db = await read_objects(License)
    assert len(licenses_in_db) == 1
    assert LicenseRow.model_validate(licenses_in_db[0]).in_use == one_license_in_use.quantity

    await remove_license_in_use(synth_session, inserted[0].id)

    licenses_in_db_after_delete = await read_objects(License)
    assert len(licenses_in_db_after_delete) == 1
    assert LicenseRow.model_validate(licenses_in_db_after_delete[0]).in_use == 0
