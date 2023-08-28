"""
Test Slurm cmd_utils.
"""
from textwrap import dedent
from typing import List
from unittest import mock

from pytest import fixture, mark, raises

from lm_agent.workload_managers.slurm.cmd_utils import (
    LicenseBooking,
    SqueueParserUnexpectedInputError,
    _match_requested_license,
    get_all_features_used_values,
    get_all_product_features_from_cluster,
    get_required_licenses_for_job,
    squeue_parser,
)


@fixture
def job_licenses_good() -> str:
    return "testproduct1.test-feature1@flexlm:11,testproduct2.testfeature2@flexlm:22,testproduct3.testfeature3@flexlm:33"


@fixture
def job_licenses_bad() -> str:
    return ""


def test_squeue_with_bad_input():
    """Test that squeue throws the correct exception given incorrect input."""
    with raises(SqueueParserUnexpectedInputError):
        _ = squeue_parser("bad input")


def test_squeue_parser_returns_correct_output_format():
    """Given the squeue formatted output, ensure the `squeue_parsed()` returns the expected values."""
    squeue_parsed_output = [
        {"job_id": 1, "run_time_in_seconds": 300, "state": "RUNNING"},
        {"job_id": 2, "run_time_in_seconds": 184981, "state": "RUNNING"},
        {"job_id": 3, "run_time_in_seconds": 17084, "state": "RUNNING"},
    ]
    squeue_parsed = squeue_parser(
        "\n".join(
            [
                "1|5:00|RUNNING",
                "2|2-3:23:01|RUNNING",
                "3|4:44:44|RUNNING",
            ]
        )
    )
    assert squeue_parsed == squeue_parsed_output


@mark.parametrize(
    "license,output",
    [
        (
            "product.feature@flexlm:123",
            {
                "product_feature": "product.feature",
                "server_type": "flexlm",
                "tokens": 123,
            },
        ),
        (
            "product.feature@rlm",
            {
                "product_feature": "product.feature",
                "server_type": "rlm",
                "tokens": 1,
            },
        ),
        (
            "product.feature-123@flexlm",
            {
                "product_feature": "product.feature-123",
                "server_type": "flexlm",
                "tokens": 1,
            },
        ),
        (
            "product-123.feature@rlm",
            {
                "product_feature": "product-123.feature",
                "server_type": "rlm",
                "tokens": 1,
            },
        ),
    ],
)
def test_match_requested_license(license, output):
    requested_license = license

    return_value = _match_requested_license(requested_license)

    assert return_value == output


@mark.parametrize(
    "requested_license",
    [
        ("productfeature@flexlm:bla"),
        ("productfeature@flexlm:999"),
        ("product.featureflexlm:999"),
        ("productfeatureflexlm999"),
        (""),
        ("product.feature:flexlm@999"),
    ],
)
def test_match_requested_license_wrong_string(requested_license):
    assert _match_requested_license(requested_license) == None


def test_get_required_licenses_for_job_good(job_licenses_good: str):
    """
    Do I return the correct licenses when the license format matches?
    """
    required_licenses = get_required_licenses_for_job(job_licenses_good)
    assert len(required_licenses) == 3
    assert required_licenses == [
        LicenseBooking(
            product_feature="testproduct1.test-feature1",
            quantity=11,
        ),
        LicenseBooking(
            product_feature="testproduct2.testfeature2",
            quantity=22,
        ),
        LicenseBooking(
            product_feature="testproduct3.testfeature3",
            quantity=33,
        ),
    ]


def test_get_required_licenses_for_job_bad(job_licenses_bad: None):
    """
    Do I return the correct licenses when the license format doesn't match?
    """
    required_licenses = get_required_licenses_for_job(job_licenses_bad)
    assert len(required_licenses) == 0
    assert required_licenses == []


@mark.asyncio
@mark.parametrize(
    "show_lic_output,features_from_cluster",
    [
        (
            dedent(
                """
                LicenseName=testproduct1.feature1@flexlm
                    Total=10 Used=0 Free=10 Reserved=0 Remote=yes
                """
            ),
            ["testproduct1.feature1"],
        ),
        (
            dedent(
                """
                LicenseName=product_name.feature_name@flexlm
                    Total=10 Used=0 Free=10 Reserved=0 Remote=yes
                """
            ),
            ["product_name.feature_name"],
        ),
        (
            dedent(
                """
                LicenseName=converge.converge_super@rlm
                    Total=9 Used=0 Free=9 Reserved=0 Remote=yes
                LicenseName=converge.converge_tecplot@rlm
                    Total=45 Used=0 Free=45 Reserved=0 Remote=yes
                """
            ),
            ["converge.converge_super", "converge.converge_tecplot"],
        ),
        (
            dedent(
                """
                LicenseName=powerflow.powerflow-disc@rlm
                    Total=9 Used=0 Free=9 Reserved=0 Remote=yes
                """
            ),
            ["powerflow.powerflow-disc"],
        ),
        ("", []),
    ],
)
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
async def test_get_product_features_from_cluster(
    show_lic_mock: mock.MagicMock, show_lic_output: str, features_from_cluster: List[str]
):
    show_lic_mock.return_value = show_lic_output
    assert features_from_cluster == await get_all_product_features_from_cluster()


@mark.asyncio
@mark.parametrize(
    "show_lic_output,used_features",
    [
        (
            dedent(
                """
                LicenseName=abaqus.abaqus@flexlm
                    Total=1000 Used=90 Free=910 Reserved=0 Remote=yes
                LicenseName=product_name.feature_name@flexlm
                    Total=10 Used=0 Free=10 Reserved=0 Remote=yes
                LicenseName=converge.converge_super@rlm
                    Total=9 Used=1 Free=9 Reserved=0 Remote=yes
                LicenseName=converge.converge_tecplot@rlm
                    Total=45 Used=12 Free=45 Reserved=0 Remote=yes
                """
            ),
            {
                "abaqus.abaqus": 90,
                "product_name.feature_name": 0,
                "converge.converge_super": 1,
                "converge.converge_tecplot": 12,
            },
        ),
        (
            "",
            {},
        ),
    ],
)
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
async def test_get_all_features_used_values(
    show_lic_mock: mock.MagicMock, show_lic_output: str, used_features: dict
):
    show_lic_mock.return_value = show_lic_output
    assert used_features == await get_all_features_used_values()
