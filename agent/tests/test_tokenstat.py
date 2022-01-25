from textwrap import dedent
from typing import List
from unittest import mock

from pytest import fixture, mark, raises

from lm_agent import tokenstat
from lm_agent.backend_utils import BackendConfigurationRow
from lm_agent.config import settings


@fixture
def one_configuration_row_flexlm():
    return BackendConfigurationRow(
        product="testproduct",
        features={"testfeature": 10},
        license_servers=["flexlm:127.0.0.1:2345"],
        license_server_type="flexlm",
        grace_time=10000,
    )


@fixture
def one_configuration_row_rlm():
    return BackendConfigurationRow(
        product="converge",
        features={"super": 10},
        license_servers=["rlm:127.0.0.1:2345"],
        license_server_type="rlm",
        grace_time=10000,
    )


@fixture
def flexlm_server(one_configuration_row_flexlm):
    return tokenstat.FlexLMLicenseServer(one_configuration_row_flexlm.license_servers)


@fixture
def rlm_server(one_configuration_row_rlm):
    return tokenstat.RLMLicenseServer(one_configuration_row_rlm.license_servers)


@fixture
def scontrol_show_lic_output_flexlm():
    return dedent(
        """
        LicenseName=testproduct.testfeature@flexlm
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


def test_get_flexlm_commands_list(flexlm_server):
    """
    Do the commands for invoking the license server have the correct data?
    """
    commands_list = flexlm_server.get_commands_list()
    assert commands_list == [f"{settings.LMUTIL_PATH} lmstat -c 2345@127.0.0.1 -f"]


def test_get_rlm_commands_list(rlm_server):
    """
    Do the commands for invoking the license server have the correct data?
    """
    commands_list = rlm_server.get_commands_list()
    assert commands_list == [f"{settings.RLMUTIL_PATH} rlmstat -c 2345@127.0.0.1 -a -p"]


@mark.asyncio
@mock.patch("lm_agent.tokenstat.asyncio.wait_for")
@mock.patch("lm_agent.tokenstat.asyncio.create_subprocess_shell")
async def test_flexlm_get_output_from_server(
    create_subprocess_mock: mock.MagicMock,
    wait_for_mock: mock.MagicMock,
    flexlm_server,
    lm_output,
):
    """
    Do the license server interface return the output from the license server?
    """
    proc_mock = mock.MagicMock()
    proc_mock.returncode = 0

    create_subprocess_mock.return_value = proc_mock
    wait_for_mock.return_value = (
        bytes(lm_output, encoding="UTF8"),
        None,
    )

    output = await flexlm_server.get_output_from_server("testproduct.testfeature")
    assert output == lm_output


@mark.asyncio
@mock.patch("lm_agent.tokenstat.asyncio.wait_for")
@mock.patch("lm_agent.tokenstat.asyncio.create_subprocess_shell")
async def test_rlm_get_output_from_server(
    create_subprocess_mock: mock.MagicMock,
    wait_for_mock: mock.MagicMock,
    rlm_server,
    rlm_output,
):
    """
    Do the license server interface return the output from the license server?
    """
    proc_mock = mock.MagicMock()
    proc_mock.returncode = 0

    create_subprocess_mock.return_value = proc_mock
    wait_for_mock.return_value = (
        bytes(rlm_output, encoding="UTF8"),
        None,
    )

    output = await rlm_server.get_output_from_server()
    assert output == rlm_output


@mark.asyncio
@mock.patch("lm_agent.tokenstat.FlexLMLicenseServer.get_output_from_server")
async def test_flexlm_get_report_item(get_output_from_server_mock: mock.MagicMock, flexlm_server, lm_output):
    """
    Do the FlexLM server interface generate a report item for the product?
    """
    get_output_from_server_mock.return_value = lm_output

    assert await flexlm_server.get_report_item("testproduct.testfeature") == tokenstat.LicenseReportItem(
        product_feature="testproduct.testfeature",
        used=93,
        total=1000,
        used_licenses=[
            {"booked": 29, "user_name": "jbemfv", "lead_host": "myserver.example.com"},
            {"booked": 27, "user_name": "cdxfdn", "lead_host": "myserver.example.com"},
            {"booked": 37, "user_name": "jbemfv", "lead_host": "myserver.example.com"},
        ],
    )


@mark.asyncio
@mock.patch("lm_agent.tokenstat.RLMLicenseServer.get_output_from_server")
async def test_rlm_get_report_item(get_output_from_server_mock: mock.MagicMock, rlm_server, rlm_output):
    """
    Do the RLM server interface generate a report item for the product?
    """
    get_output_from_server_mock.return_value = rlm_output

    assert await rlm_server.get_report_item("converge.super") == tokenstat.LicenseReportItem(
        product_feature="converge.super",
        used=93,
        total=1000,
        used_licenses=[
            {"booked": 29, "user_name": "jbemfv", "lead_host": "myserver.example.com"},
            {"booked": 27, "user_name": "cdxfdn", "lead_host": "myserver.example.com"},
            {"booked": 37, "user_name": "jbemfv", "lead_host": "myserver.example.com"},
        ],
    )


@mark.asyncio
@mock.patch("lm_agent.tokenstat.FlexLMLicenseServer.get_output_from_server")
async def test_flexlm_get_report_item_with_bad_output(
    get_output_from_server_mock: mock.MagicMock, flexlm_server, lm_output_bad
):
    get_output_from_server_mock.return_value = lm_output_bad

    with raises(tokenstat.LicenseManagerBadServerOutput):
        await flexlm_server.get_report_item("testproduct.testfeature")


@mark.asyncio
@mock.patch("lm_agent.tokenstat.RLMLicenseServer.get_output_from_server")
async def test_rlm_get_report_item_with_no_used_licenses(
    get_output_from_server_mock: mock.MagicMock, rlm_server, rlm_output_no_licenses
):
    get_output_from_server_mock.return_value = rlm_output_no_licenses

    assert await rlm_server.get_report_item("converge.super") == tokenstat.LicenseReportItem(
        product_feature="converge.super",
        used=0,
        total=1000,
        used_licenses=[],
    )


@mark.asyncio
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "lm_output",
            [
                {
                    "product_feature": "testproduct.testfeature",
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
    ],
)
@mock.patch("lm_agent.tokenstat.FlexLMLicenseServer.get_output_from_server")
@mock.patch("lm_agent.tokenstat.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_flexlm_get_report(
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    get_output_from_server_mock: mock.MagicMock,
    output,
    reconciliation,
    one_configuration_row_flexlm,
    scontrol_show_lic_output_flexlm,
    request,
):
    """
    Do I get a report for the FlexLM licenses in the cluster?
    """
    get_config_from_backend_mock.return_value = [one_configuration_row_flexlm]
    show_lic_mock.return_value = scontrol_show_lic_output_flexlm

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output

    reconcile_list = await tokenstat.report()
    assert reconcile_list == reconciliation


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
@mock.patch("lm_agent.tokenstat.RLMLicenseServer.get_output_from_server")
@mock.patch("lm_agent.tokenstat.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_rlm_get_report(
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    get_output_from_server_mock: mock.MagicMock,
    output,
    reconciliation,
    one_configuration_row_rlm,
    scontrol_show_lic_output_rlm,
    request,
):
    """
    Do I get a report for the RLM licenses in the cluster?
    """
    get_config_from_backend_mock.return_value = [one_configuration_row_rlm]
    show_lic_mock.return_value = scontrol_show_lic_output_rlm

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output

    reconcile_list = await tokenstat.report()
    assert reconcile_list == reconciliation


@mark.asyncio
@mock.patch("lm_agent.tokenstat.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_flexlm_report_with_empty_backend(
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_flexlm,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_config_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_flexlm

    reconcile_list = await tokenstat.report()
    assert reconcile_list == []


@mark.asyncio
@mock.patch("lm_agent.tokenstat.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_rlm_report_with_empty_backend(
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_rlm,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_config_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_rlm

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
