"""
Tests of Prolog
"""
from typing import List
from pytest import fixture, mark
from unittest import mock
from licensemanager2.workload_managers.slurm.cmd_utils import (
    get_required_licenses_for_job,
)


@fixture
def scontrol_parsed_output_good() -> List[str]:
    return [
        "TESTPRODUCT.TESTFEATURE@flexlm:11",
        "TESTPRODUCT2.TESTFEATURE2@flexlm:22",
        "TESTPRODUCT3.TESTFEATURE3@flexlm:33",
    ]


@fixture
def scontrol_parsed_output_bad() -> List[str]:
    return [
        "TESTFEATURE@flexlm:11",
        "TESTPRODUCT2@22",
        "TESTFEATURE3@flexlm",
    ]


@fixture
def slurm_job_id() -> str:
    return "777"


@mark.asyncio
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.get_licenses_for_job")
async def test_get_required_licenses_for_job_good(
    get_licenses_for_job_mock: mock.MagicMock,
    slurm_job_id: str, scontrol_parsed_output_good: List[str]
):
    """
    Do I return the correct licenses when the license format matches?
    """
    get_licenses_for_job_mock.return_value = scontrol_parsed_output_good
    license_booking_request = await get_required_licenses_for_job(
        slurm_job_id
    )
    assert len(license_booking_request.bookings) == 3


@mark.asyncio
@mock.patch("licensemanager2.workload_managers.slurm.cmd_utils.get_licenses_for_job")
async def test_get_required_licenses_for_job_bad(
    get_licenses_for_job_mock: mock.MagicMock,
    slurm_job_id: str, scontrol_parsed_output_bad: List[str]
):
    """
    Do I return the correct licenses when the license format doesn't match?
    """

    get_licenses_for_job_mock.return_value = scontrol_parsed_output_bad
    license_booking_request = await get_required_licenses_for_job(
        slurm_job_id
    )
    assert len(license_booking_request.bookings) == 0