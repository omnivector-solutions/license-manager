"""
Tests of Prolog
"""

from typing import List
# from unittest.mock import patch
from pytest import fixture, mark


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


@mark.asyncio
async def test_get_required_licenses_for_job():
    """
    Do I collect the requested structured data from running all these dang tools?
    """
    p0 = patch.object(
        cmd_utils,
        "scontrol_show_lic",
        scontrol_output_good_format
    )
    with p0:
        licenses = await slurmctld_prolog._get_required_licenses_for_job()
        assert len(licenses) == 3
    

@mark.asyncio
async def test_get_required_licenses_for_job():
    """
    Do I collect the requested structured data from running all these dang tools?
    """
    assert (0 == 1)