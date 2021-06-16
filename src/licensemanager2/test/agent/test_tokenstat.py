"""
Tests of tokenstat
"""
from pathlib import Path
from unittest import mock
from unittest.mock import patch
from pytest import fixture, mark, raises

from licensemanager2.agent import tokenstat
from licensemanager2.agent.parsing import flexlm
from licensemanager2.test.agent.conftest import MOCK_BIN_PATH
from licensemanager2.workload_managers.slurm import cmd_utils


@fixture
def license_server_features():
    """
    The license server type, product and features.
    """
    return [{
        "features": ["TESTFEATURE"],
        "license_server_type": "flexlm",
        "product": "TESTPRODUCT"
    }]


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


def test_lri_from_stdout():
    """
    Do I parse the stdout string from flexlm to produce structured data?
    """
    stdout = "Users of TESTFEATURE:  (Total of 1000 licenses issued;  Total of 502 licenses in use)"
    lri = tokenstat.LicenseReportItem.from_stdout(
        product="TESTPRODUCT",
        parse_fn=flexlm.parse,
        tool_name="flexlm",
        stdout=stdout,
    )
    assert lri == tokenstat.LicenseReportItem(
        tool_name="flexlm",
        product_feature="TESTPRODUCT.TESTFEATURE",
        used=502,
        total=1000,
    )


def test_tooloptions_cmd_list(
    tool_opts: tokenstat.ToolOptions, one_configuration_row
):
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
        product_feature="TESTPRODUCT.TESTFEATURE", used=502, total=1000
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
@mock.patch("licensemanager2.agent.tokenstat.get_config_from_backend")
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
    p0 = patch.object(
        cmd_utils,
        "get_tokens_for_license",
        0
    )
    p1 = patch.dict(
        tokenstat.ToolOptionsCollection.tools,
        {"flexlm": tool_opts}
    )
    license_report_item = {
        "product_feature": "testproduct1.TESTFEATURE",
        "used": 502,
        "total": 1000
    }
    with p0, p1:
        assert [license_report_item] == await tokenstat.report()
