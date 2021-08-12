from pytest import raises

from lm_agent.workload_managers.slurm.cmd_utils import (
    SqueueParserUnexpectedInputError,
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
