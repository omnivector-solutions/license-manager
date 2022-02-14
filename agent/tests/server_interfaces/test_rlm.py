"""Test the RLM license server interface."""
from unittest import mock

from pytest import fixture, mark

from lm_agent.config import settings
from lm_agent.server_interfaces.license_server_interface import LicenseReportItem
from lm_agent.server_interfaces.rlm import RLMLicenseServer


@fixture
def rlm_server(one_configuration_row_rlm):
    return RLMLicenseServer(one_configuration_row_rlm.license_servers)


def test_get_rlm_commands_list(rlm_server):
    """
    Do the commands for invoking the license server have the correct data?
    """
    commands_list = rlm_server.get_commands_list()
    assert commands_list == [f"{settings.RLMUTIL_PATH} rlmstat -c 2345@127.0.0.1 -a -p"]


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.rlm.run_command")
async def test_rlm_get_output_from_server(
    run_command_mock: mock.MagicMock,
    rlm_server,
    rlm_output,
):
    """
    Do the license server interface return the output from the license server?
    """
    run_command_mock.return_value = rlm_output

    output = await rlm_server.get_output_from_server()
    assert output == rlm_output


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.rlm.RLMLicenseServer.get_output_from_server")
async def test_rlm_get_report_item(get_output_from_server_mock: mock.MagicMock, rlm_server, rlm_output):
    """
    Do the RLM server interface generate a report item for the product?
    """
    get_output_from_server_mock.return_value = rlm_output

    assert await rlm_server.get_report_item("converge.super") == LicenseReportItem(
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
@mock.patch("lm_agent.server_interfaces.rlm.RLMLicenseServer.get_output_from_server")
async def test_rlm_get_report_item_with_no_used_licenses(
    get_output_from_server_mock: mock.MagicMock, rlm_server, rlm_output_no_licenses
):
    get_output_from_server_mock.return_value = rlm_output_no_licenses

    assert await rlm_server.get_report_item("converge.super") == LicenseReportItem(
        product_feature="converge.super",
        used=0,
        total=1000,
        used_licenses=[],
    )
