from pytest import mark, raises

from lm_agent.workload_managers.slurm.cmd_utils import (
    SqueueParserUnexpectedInputError,
    _match_requested_license,
    squeue_parser,
)


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


def test_match_requested_license():
    requested_license = "product.feature@flexlm:123"

    return_value = _match_requested_license(requested_license)

    assert return_value == {
        "product_feature": "product.feature",
        "server_type": "flexlm",
        "tokens": 123,
    }


@mark.parametrize(
    "requested_license",
    [
        ("productfeature@flexlm:bla"),
        ("productfeature@flexlm:999"),
        ("product.featureflexlm:999"),
        ("product.feature@flexlm999"),
        ("productfeatureflexlm999"),
        (""),
        ("product.feature:flexlm@999"),
    ],
)
def test_match_requested_license_wrong_string(requested_license):
    assert _match_requested_license(requested_license) == None
