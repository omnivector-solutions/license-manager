"""
Test Slurm cmd_utils.
"""
from pytest import fixture, mark, raises

from lm_agent.workload_managers.slurm.cmd_utils import (
    LicenseBooking,
    SqueueParserUnexpectedInputError,
    _match_requested_license,
    get_required_licenses_for_job,
    squeue_parser,
)


@fixture
def job_licenses_good() -> str:
    return "testproduct.testfeature@flexlm:11,testproduct2.testfeature2@flexlm:22,testproduct3.testfeature3@flexlm:33"


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
            product_feature="testproduct.testfeature",
            tokens=11,
            license_server_type="flexlm",
        ),
        LicenseBooking(
            product_feature="testproduct2.testfeature2",
            tokens=22,
            license_server_type="flexlm",
        ),
        LicenseBooking(
            product_feature="testproduct3.testfeature3",
            tokens=33,
            license_server_type="flexlm",
        ),
    ]


def test_get_required_licenses_for_job_bad(job_licenses_bad: None):
    """
    Do I return the correct licenses when the license format doesn't match?
    """
    required_licenses = get_required_licenses_for_job(job_licenses_bad)
    assert len(required_licenses) == 0
    assert required_licenses == []
