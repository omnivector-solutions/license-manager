"""
Tests of Prolog
"""
from typing import List
# from unittest.mock import patch
from pytest import fixture, mark
from unittest.mock import patch
from licensemanager2.workload_managers.slurm.slurmctld_prolog import (
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
async def test_get_required_licenses_for_job_good(slurm_job_id: str, scontrol_parsed_output_good: List[str]):
    """
    Do I return the correct licenses when the license format matches?
    """
    p1 = patch(
        'licensemanager2.workload_managers.slurm.slurmctld_prolog.get_licenses_for_job',
        return_value=scontrol_parsed_output_good
    )
    with p1:
        license_booking_request = await get_required_licenses_for_job(
            slurm_job_id
        )
        assert len(license_booking_request.bookings) == 3


@mark.asyncio
async def test_get_required_licenses_for_job_bad(slurm_job_id: str, scontrol_parsed_output_bad: List[str]):
    """
    Do I return the correct licenses when the license format doesn't match?
    """
    p1 = patch(
        'licensemanager2.workload_managers.slurm.slurmctld_prolog.get_licenses_for_job',
        return_value=scontrol_parsed_output_bad
    )
    with p1:
        license_booking_request = await get_required_licenses_for_job(
            slurm_job_id
        )
        assert len(license_booking_request.bookings) == 0