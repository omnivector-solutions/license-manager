"""
Tests of tokenstat
"""
from pathlib import Path
from unittest.mock import patch

from pytest import fixture, mark, raises

from licensemanager2.agent import tokenstat
from licensemanager2.agent.parsing import flexlm
from licensemanager2.agent.settings import SETTINGS
from licensemanager2.test.agent.conftest import MOCK_BIN_PATH


@fixture
def service_env_string() -> str:
    """
    A collection of service definitions from an env string
    """
    return "flexlm:172.0.1.2:2345 flexlm:172.0.1.3:2345 xyz:172.0.1.2:7171"


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


def test_lsc_from_env_string(service_env_string: str):
    """
    Do I parse the env string to produce a good service?
    """
    lsc = tokenstat.LicenseServiceCollection.from_env_string(service_env_string)
    assert lsc.services == {
        "flexlm": tokenstat.LicenseService(
            name="flexlm", hostports=[("172.0.1.2", 2345), ("172.0.1.3", 2345)]
        ),
        "xyz": tokenstat.LicenseService(name="xyz", hostports=[("172.0.1.2", 7171)]),
    }


def test_lri_from_stdout():
    """
    Do I parse the stdout string from flexlm to produce structured data?
    """
    stdout = "Users of abaqus:  (Total of 1000 licenses issued;  Total of 502 licenses in use)"
    lri = tokenstat.LicenseReportItem.from_stdout(
        parse_fn=flexlm.parse,
        tool_name="flexlm",
        stdout=stdout,
    )
    assert lri == tokenstat.LicenseReportItem(
        tool_name="flexlm",
        product_feature="PRODUCT.abaqus",
        used=502,
        total=1000,
    )


def test_tooloptions_cmd_list(
    tool_opts: tokenstat.ToolOptions, service_env_string: str
):
    """
    Do I produce a reasonable set of command lines from the tool definitions
    """
    with patch.object(SETTINGS, "SERVICE_ADDRS", service_env_string):
        assert tool_opts.cmd_list() == [
            f"{MOCK_BIN_PATH}/lmstat 172.0.1.2 2345",
            f"{MOCK_BIN_PATH}/lmstat 172.0.1.3 2345",
        ]


@mark.asyncio
async def test_attempt_tool_checks(
    tool_opts: tokenstat.ToolOptions, service_env_string: str
):
    """
    Do I run the commands corresponding to my collection of tools and service definitions?
    """
    # good tool
    with patch.object(SETTINGS, "SERVICE_ADDRS", service_env_string):
        ret = await tokenstat.attempt_tool_checks(tool_opts)
        assert ret == tokenstat.LicenseReportItem(
            tool_name="flexlm", product_feature="PRODUCT.abaqus", used=502, total=1000
        )

    # bad tool
    tool_opts.args = "{exe} fail"
    with patch.object(SETTINGS, "SERVICE_ADDRS", service_env_string):
        with raises(RuntimeError):
            await tokenstat.attempt_tool_checks(tool_opts)


@mark.asyncio
async def test_report(tool_opts: tokenstat.ToolOptions, service_env_string: str):
    """
    Do I collect the requested structured data from running all these dang tools?
    """
    p1 = patch.dict(tokenstat.ToolOptionsCollection.tools, {"flexlm": tool_opts})
    p2 = patch.object(SETTINGS, "SERVICE_ADDRS", service_env_string)
    with p1, p2:
        assert [
            {"product_feature": "PRODUCT.abaqus", "used": 502, "total": 1000}
        ] == await tokenstat.report()
