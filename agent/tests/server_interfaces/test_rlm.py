"""Test the RLM license server interface."""
import shlex
from unittest import mock

from pytest import fixture, mark, raises

from lm_agent.backend_utils import BackendConfigurationRow
from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBadServerOutput
from lm_agent.server_interfaces.license_server_interface import LicenseReportItem
from lm_agent.server_interfaces.rlm import RLMLicenseServer


@fixture
def rlm_server(one_configuration_row_rlm: BackendConfigurationRow):
    return RLMLicenseServer(one_configuration_row_rlm.license_servers)


def test_get_rlm_commands_list(rlm_server: RLMLicenseServer):
    """
    Do the commands for invoking the license server have the correct data?
    """
    commands_list = rlm_server.get_commands_list()
    assert shlex.join(commands_list[0]) == f"{settings.RLMUTIL_PATH} rlmstat -c 2345@127.0.0.1 -a -p"


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.rlm.run_command")
async def test_rlm_get_output_from_server(
    run_command_mock: mock.MagicMock,
    rlm_server: RLMLicenseServer,
    rlm_output: str,
):
    """
    Do the license server interface return the output from the license server?
    """
    run_command_mock.return_value = rlm_output

    output = await rlm_server.get_output_from_server()
    assert output == rlm_output


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.rlm.RLMLicenseServer.get_output_from_server")
async def test_rlm_get_report_item(
    get_output_from_server_mock: mock.MagicMock, rlm_server: RLMLicenseServer, rlm_output: str
):
    """
    Do the RLM server interface generate a report item for the product?
    """
    get_output_from_server_mock.return_value = rlm_output

    assert await rlm_server.get_report_item("converge.converge_super") == LicenseReportItem(
        product_feature="converge.converge_super",
        used=93,
        total=1000,
        used_licenses=[
            {"booked": 29, "user_name": "jbemfv", "lead_host": "myserver.example.com"},
            {"booked": 27, "user_name": "cdxfdn", "lead_host": "myserver.example.com"},
            {"booked": 37, "user_name": "jbemfv", "lead_host": "myserver.example.com"},
        ],
    )


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.rlm.RLMLicenseServer.get_output_from_server")
async def test_rlm_get_report_item_with_bad_output(
    get_output_from_server_mock: mock.MagicMock, rlm_server: RLMLicenseServer, lsdyna_output_bad: str
):
    """
    Do the RLM server interface raise an exception when the server returns an unparseable output?
    """
    get_output_from_server_mock.return_value = lsdyna_output_bad

    with raises(LicenseManagerBadServerOutput):
        await rlm_server.get_report_item("converge.converge_super")


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.rlm.RLMLicenseServer.get_output_from_server")
async def test_rlm_get_report_item_with_no_used_licenses(
    get_output_from_server_mock: mock.MagicMock, rlm_server: RLMLicenseServer, rlm_output_no_licenses: str
):
    """
    Do the RLM server interface generate a report item when no licenses are in use?
    """
    get_output_from_server_mock.return_value = rlm_output_no_licenses

    assert await rlm_server.get_report_item("converge.converge_super") == LicenseReportItem(
        product_feature="converge.converge_super",
        used=0,
        total=1000,
        used_licenses=[],
    )
