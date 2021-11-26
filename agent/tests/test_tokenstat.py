from pathlib import Path
from textwrap import dedent
from typing import List
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
            product="converge",
            features={"super": 10},
            license_servers=["rlm:127.0.0.1:2345"],
            license_server_type="rlm",
            grace_time=10000,
        )
    ]


@fixture
def scontrol_show_lic_output():
    return dedent(
        """
        LicenseName=testproduct1.feature1@flexlm
            Total=10 Used=0 Free=10 Reserved=0 Remote=yes
        """
    )


@fixture
def scontrol_show_lic_output_rlm():
    return dedent(
        """
        LicenseName=converge.super@rlm
            Total=10 Used=0 Free=10 Reserved=0 Remote=yes
        """
    )


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
    return [{"features": ["super"], "license_server_type": "rlm", "product": "converge"}]


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
        path=MOCK_BIN_PATH / "rlmstat",
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
@mock.patch("lm_agent.tokenstat.scontrol_show_lic")
async def test_report(
    show_lic_mock: mock.MagicMock,
    get_config_from_backend_mock: mock.MagicMock,
    tool_opts: tokenstat.ToolOptions,
    one_configuration_row,
    scontrol_show_lic_output,
):
    """
    Do I collect the requested structured data from running all these dang tools?
    """
    get_config_from_backend_mock.return_value = one_configuration_row
    show_lic_mock.return_value = scontrol_show_lic_output

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
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "rlm_output",
            [
                {
                    "product_feature": "converge.super",
                    "used": 93,
                    "total": 1000,
                    "used_licenses": [
                        {
                            "user_name": "jbemfv",
                            "lead_host": "myserver.example.com",
                            "booked": 29,
                        },
                        {
                            "user_name": "cdxfdn",
                            "lead_host": "myserver.example.com",
                            "booked": 27,
                        },
                        {
                            "user_name": "jbemfv",
                            "lead_host": "myserver.example.com",
                            "booked": 37,
                        },
                    ],
                },
            ],
        ),
        (
            "rlm_output_no_licenses",
            [
                {
                    "product_feature": "converge.super",
                    "used": 0,
                    "total": 1000,
                    "used_licenses": [],
                },
            ],
        ),
    ],
)
@mock.patch("lm_agent.tokenstat.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
@mock.patch("lm_agent.tokenstat.asyncio.create_subprocess_shell")
@mock.patch("lm_agent.tokenstat.asyncio.wait_for")
@mock.patch("lm_agent.tokenstat.ToolOptionsCollection")
async def test_report_rlm(
    tools_mock: mock.MagicMock,
    wait_for_mock: mock.AsyncMock,
    create_subprocess_mock: mock.AsyncMock,
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    output,
    reconciliation,
    tool_opts_rlm: tokenstat.ToolOptions,
    one_configuration_row_rlm,
    scontrol_show_lic_output_rlm,
    request,
):
    """
    Do I collect the requested structured data from running all these dang tools?
    """
    proc_mock = mock.MagicMock()
    proc_mock.returncode = 0
    create_subprocess_mock.return_value = proc_mock
    get_config_from_backend_mock.return_value = one_configuration_row_rlm
    show_lic_mock.return_value = scontrol_show_lic_output_rlm

    tools_mock.tools = {"rlm": tool_opts_rlm}
    output = request.getfixturevalue(output)

    wait_for_mock.return_value = (
        bytes(output, encoding="UTF8"),
        None,
    )
    reconcile_list = await tokenstat.report()
    assert reconcile_list == reconciliation


@mark.asyncio
@mock.patch("lm_agent.tokenstat.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
@mock.patch("lm_agent.tokenstat.asyncio.create_subprocess_shell")
@mock.patch("lm_agent.tokenstat.ToolOptionsCollection")
async def test_report_rlm_empty_backend(
    tools_mock: mock.MagicMock,
    create_subprocess_mock: mock.AsyncMock,
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    tool_opts_rlm: tokenstat.ToolOptions,
    scontrol_show_lic_output_rlm,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    proc_mock = mock.MagicMock()
    proc_mock.returncode = 0
    create_subprocess_mock.return_value = proc_mock
    get_config_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_rlm

    tools_mock.tools = {"rlm": tool_opts_rlm}

    reconcile_list = await tokenstat.report()
    assert reconcile_list == []


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
                LicenseName=converge_super@rlm
                    Total=9 Used=0 Free=9 Reserved=0 Remote=yes
                LicenseName=converge_tecplot@rlm
                    Total=45 Used=0 Free=45 Reserved=0 Remote=yes
                """
            ),
            ["converge.super", "converge.tecplot"],
        ),
        ("", []),
    ],
)
def test_get_product_features_from_cluster(show_lic_output: str, features_from_cluster: List[str]):
    assert features_from_cluster == tokenstat.get_all_product_features_from_cluster(show_lic_output)


def test_get_local_license_configurations():
    configuration_super = BackendConfigurationRow(
        product="converge",
        features={"super": 10},
        license_servers=["rlm:127.0.0.1:2345"],
        license_server_type="rlm",
        grace_time=10000,
    )

    configuration_polygonica = BackendConfigurationRow(
        product="converge",
        features={"polygonica": 10},
        license_servers=["rlm:127.0.0.1:2345"],
        license_server_type="rlm",
        grace_time=10000,
    )

    license_configurations = [configuration_super, configuration_polygonica]
    local_licenses = ["converge.super"]

    assert tokenstat.get_local_license_configurations(license_configurations, local_licenses) == [
        configuration_super
    ]
