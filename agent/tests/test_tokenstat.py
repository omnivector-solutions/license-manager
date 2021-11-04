from pathlib import Path
from unittest import mock
from unittest.mock import patch

from pytest import fixture, mark, raises

from lm_agent import tokenstat
from lm_agent.backend_utils import BackendConfigurationRow
from lm_agent.parsing import flexlm, rlm
from lm_agent.workload_managers.slurm import cmd_utils
from tests.conftest import MOCK_BIN_PATH


@fixture
def one_configuration_row():
    return [
        BackendConfigurationRow(
            product="testproduct1",
            features={"feature1": 10},
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=10000,
        )
    ]


@fixture
def one_configuration_row_rlm():
    return [
        BackendConfigurationRow(
            product="feature1",
            features={"feature1": 10},
            license_servers=["rlm:127.0.0.1:2345"],
            license_server_type="rlm",
            grace_time=10000,
        )
    ]


@fixture
def license_server_features():
    """
    The license server type, product and features.
    """
    return [{"features": ["TESTFEATURE"], "license_server_type": "flexlm", "product": "TESTPRODUCT"}]


@fixture
def license_server_features_rlm():
    """
    The license server type, product and features.
    """
    return [{"features": ["TESTFEATURE"], "license_server_type": "rlm", "product": "TESTFEATURE"}]


@fixture
def tool_opts() -> tokenstat.ToolOptions:
    """
    A ToolOptions set up for easy testing
    """
    return tokenstat.ToolOptions(
        name="flexlm",
        path=Path(f"{MOCK_BIN_PATH}/lmstat"),
        args="{exe} {host} {port}",
        parse_fn=flexlm.parse,
    )


@fixture
def tool_opts_rlm() -> tokenstat.ToolOptions:
    """
    A ToolOptions set up for easy testing
    """
    return tokenstat.ToolOptions(
        name="rlm",
        path=Path(f"{MOCK_BIN_PATH}/rlmstat"),
        args="{exe} {host} {port}",
        parse_fn=rlm.parse,
    )


def test_lri_from_stdout(lm_output):
    """
    Do I parse the stdout string from flexlm to produce structured data?
    """
    lri = tokenstat.LicenseReportItem.from_stdout(
        product="TESTPRODUCT",
        parse_fn=flexlm.parse,
        tool_name="flexlm",
        stdout=lm_output,
    )
    assert lri == tokenstat.LicenseReportItem(
        tool_name="flexlm",
        product_feature="TESTPRODUCT.TESTFEATURE",
        used=93,
        total=1000,
        used_licenses=[
            {"booked": 29, "user_name": "jbemfv", "lead_host": "myserver.example.com"},
            {"booked": 27, "user_name": "cdxfdn", "lead_host": "myserver.example.com"},
            {"booked": 37, "user_name": "jbemfv", "lead_host": "myserver.example.com"},
        ],
    )


def test_tooloptions_cmd_list(tool_opts: tokenstat.ToolOptions, one_configuration_row):
    """
    Do I produce a reasonable set of command lines from the tool definitions
    """
    assert tool_opts.cmd_list(one_configuration_row[0].license_servers) == [
        f"{MOCK_BIN_PATH}/lmstat 127.0.0.1 2345",
    ]


@mark.asyncio
async def test_attempt_tool_checks(
    tool_opts: tokenstat.ToolOptions,
):
    """
    Do I run the commands corresponding to my collection of tools and service definitions?
    """
    # good tool

    ret = await tokenstat.attempt_tool_checks(
        tool_opts,
        "TESTPRODUCT",
        "TESTFEATURE",
        ["flexlm:127.0.0.1:2345"],
    )
    assert ret == tokenstat.LicenseReportItem(
        tool_name="flexlm",
        product_feature="TESTPRODUCT.TESTFEATURE",
        used=502,
        total=1000,
        used_licenses=[
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 29},
            {"user_name": "cdxfdn", "lead_host": "myserver.example.com", "booked": 27},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 23},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 9},
            {"user_name": "cdxfdn", "lead_host": "myserver.example.com", "booked": 8},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 15},
            {"user_name": "cdxfdn", "lead_host": "myserver.example.com", "booked": 43},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 11},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 13},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 23},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 28},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 11},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 17},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 38},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 25},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 35},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 38},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 4},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 9},
            {"user_name": "cdxfdn", "lead_host": "myserver.example.com", "booked": 11},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 19},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 15},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 14},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 37},
        ],
    )

    # bad tool
    tool_opts.args = "{exe} fail"
    with raises(RuntimeError):
        await tokenstat.attempt_tool_checks(
            tool_opts,
            "TESTPRODUCT",
            "TESTFEATURE",
            ["flexlm:127.0.0.1:2345"],
        )


@mark.asyncio
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_report(
    get_config_from_backend_mock: mock.MagicMock,
    tool_opts: tokenstat.ToolOptions,
    one_configuration_row,
):
    """
    Do I collect the requested structured data from running all these dang tools?
    """
    get_config_from_backend_mock.return_value = one_configuration_row
    # Patch the objects needed to generate a report.
    p0 = patch.object(cmd_utils, "get_tokens_for_license", 0)
    p1 = patch.dict(tokenstat.ToolOptionsCollection.tools, {"flexlm": tool_opts})
    license_report_item = {
        "product_feature": "testproduct1.TESTFEATURE",
        "used": 502,
        "total": 1000,
        "used_licenses": [
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 29},
            {"user_name": "cdxfdn", "lead_host": "myserver.example.com", "booked": 27},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 23},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 9},
            {"user_name": "cdxfdn", "lead_host": "myserver.example.com", "booked": 8},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 15},
            {"user_name": "cdxfdn", "lead_host": "myserver.example.com", "booked": 43},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 11},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 13},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 23},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 28},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 11},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 17},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 38},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 25},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 35},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 38},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 4},
            {"user_name": "jxezha", "lead_host": "myserver.example.com", "booked": 9},
            {"user_name": "cdxfdn", "lead_host": "myserver.example.com", "booked": 11},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 19},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 15},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 14},
            {"user_name": "jbemfv", "lead_host": "myserver.example.com", "booked": 37},
        ],
    }
    with p0, p1:
        assert [license_report_item] == await tokenstat.report()



@mark.asyncio
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_report(
    get_config_from_backend_mock: mock.MagicMock,
    tool_opts_rlm: tokenstat.ToolOptions,
    one_configuration_row_rlm,
):
    """
    Do I collect the requested structured data from running all these dang tools?
    """
    get_config_from_backend_mock.return_value = one_configuration_row_rlm
    