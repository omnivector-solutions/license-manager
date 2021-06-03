"""
Tests
"""
import pytest
from pytest import fixture, mark
from unittest import mock
from textwrap import dedent

from licensemanager2.workload_managers.slurm.cmd_utils import (
    LicenseBookingRequest,
    ScontrolRetrievalFailure,
    ScontrolProcessError,
    get_required_licenses_for_job, check_feature_token_availablity,
    make_booking_request, reconcile, get_licenses_for_job,
    get_tokens_for_license,
    scontrol_show_lic,
    sacctmgr_modify_resource,
)


@fixture
def scrontrol_output():
    """
    Some lmstat output to parse
    """
    return dedent(
        """\
        LicenseName=myproduct0.myfeature0@licserver
            Total=579 Used=2 Free=577 Reserved=0 Remote=yes
        LicenseName=myproduct1.myfeature1@licserver
            Total=1 Used=0 Free=1 Reserved=0 Remote=yes
        LicenseName=myproduct2.myfeature2@licserver
            Total=6 Used=0 Free=6 Reserved=0 Remote=yes
        LicenseName=myproduct2.myfeature3@licserver
            Total=6 Used=0 Free=6 Reserved=0 Remote=yes
        """
    )


@fixture
def nonexistant_resource_to_modify():
    """
    A product, feature, and token count for a test to attempt to modify
    """
    return ["TESTPRODUCT", "TESTFEATURE", 5]


@fixture
def license_booking_request():
    """
    A license booking request object for testing make_booking_request()
    """
    lbr = LicenseBookingRequest()
    lbr.job_id = 100
    lbr.bookings = []
    return lbr


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_get_licenses_for_job_empty(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock
):
    """
    Testing if scontrol output returns licences needed for a job.
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.returncode = 0

    wait_for_mock.return_value = b"", ""

    assert await get_licenses_for_job("0") == []


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_get_licenses_for_job(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock
):
    """
    Testing if scontrol output returns licences needed for a job.
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.returncode = 0

    wait_for_mock.return_value = b"  Licenses=(123) ", ""

    assert await get_licenses_for_job("0") == ['(123)']


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_get_licenses_for_job_raises_scontrol_retrieval_failure(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock
):
    """
    Testing if scontrol output returns licences needed for a job.
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.returncode = 1

    wait_for_mock.return_value = b"  Licenses=(123) ", ""

    with pytest.raises(ScontrolRetrievalFailure):
        await get_licenses_for_job("0")


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_scrontrol_show_lic(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock
):
    """
    Testing if scontrol output returns licences needed for a job.
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.returncode = 0

    wait_for_mock.return_value = b"test_return_value", ""

    assert await scontrol_show_lic() == "test_return_value"


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_sacctmgr_modify_nonexistant_resource(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock, nonexistant_resource_to_modify
):
    """
    Testing if license resource in slurm is updated
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.rc = 0

    wait_for_mock.return_value = b"test_return_value", ""

    assert await sacctmgr_modify_resource(
        nonexistant_resource_to_modify[0],
        nonexistant_resource_to_modify[1],
        nonexistant_resource_to_modify[2],
    ) is False


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_sacctmgr_modify_existing_resource(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock
):
    """
    Testing if license resource in slurm is updated
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.returncode = 0
    wait_for_mock.return_value = b"return_value", ""

    assert await sacctmgr_modify_resource("TESTPRODUCT", "TESTFEATURE", 5) is True


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mark.asyncio
async def test_get_tokens_for_license(
    scontrol_show_lic_mock: mock.AsyncMock,
    scrontrol_output,
):
    """
    Testing if scontrol output returns licences needed for a job.
    """
    # scontrol_show_lic_mock.return_value = mock.AsyncMock()
    # scontrol_show_lic_mock.match_product_feature_server = mock.AsyncMock()
    scontrol_show_lic_mock.return_value = scrontrol_output

    assert await get_tokens_for_license("myproduct0.myfeature0@licserver", "Used") == 2


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.wait_for")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.asyncio.create_subprocess_shell")
@mark.asyncio
async def test_scrontrol_show_lic_process_error(
    create_subprocess_shell_mock: mock.AsyncMock, wait_for_mock: mock.AsyncMock
):
    """
    Testing if scontrol output raises an exception when there is a process error
    """
    create_subprocess_shell_mock.return_value = mock.AsyncMock()
    create_subprocess_shell_mock.communicate.return_value = mock.Mock()
    create_subprocess_shell_mock.return_value.returncode = 1

    wait_for_mock.return_value = b"test_return_value", ""

    with pytest.raises(ScontrolProcessError):
        await scontrol_show_lic()


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.httpx.get")
@mark.asyncio
async def test_reconcile(
    get_mock: mock.AsyncMock,
):
    """
    Testing if scontrol output returns licences needed for a job.
    """
    get_mock.return_value = mock.AsyncMock()
    get_mock.return_value = mock.Mock()
    get_mock.return_value.status_code = 200

    get_mock.resp.status_code = 200

    assert await reconcile() is True


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.httpx.put")
@mark.asyncio
async def test_make_booking_request(
    put_mock: mock.AsyncMock, license_booking_request: LicenseBookingRequest
):
    """
    Testing if scontrol output returns licences needed for a job.
    """
    put_mock.return_value = mock.AsyncMock()
    put_mock.return_value.status_code = 200

    assert await make_booking_request(license_booking_request) is True


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.httpx.get")
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.httpx.json")
@mark.asyncio
async def test_check_feature_token_availablity(
    get_mock: mock.AsyncMock,
    json_mock: mock.AsyncMock,
    license_booking_request: LicenseBookingRequest,
):
    """
    Test determining if there are sufficient tokens to fill the request
    """
    get_mock.return_value = mock.AsyncMock()
    get_mock.return_value.status_code = 200

    get_mock.resp.json = "test return value"

    assert await check_feature_token_availablity(license_booking_request) is True


@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.get_licenses_for_job")
@mark.asyncio
async def test_get_required_licenses_for_job(
    get_licenses_for_job_mock: mock.AsyncMock,
):
    """
    Testing the required licenses for a job are retrieved
    """
    test_job_id = "100"
    get_licenses_for_job_mock.return_value = mock.AsyncMock()
    get_licenses_for_job_mock.return_value = []  # check actual return value to construct this

    assert await get_required_licenses_for_job(test_job_id) is True