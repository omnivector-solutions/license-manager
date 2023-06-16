"""Test the FlexLM license server interface."""

import shlex
from unittest import mock

from pytest import fixture, mark, raises

from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBadServerOutput
from lm_agent.server_interfaces.flexlm import FlexLMLicenseServer
from lm_agent.server_interfaces.license_server_interface import LicenseReportItem


@fixture
def flexlm_server(one_configuration_row_flexlm) -> FlexLMLicenseServer:
    return FlexLMLicenseServer(one_configuration_row_flexlm.license_servers)


def test_get_flexlm_commands_list(flexlm_server: FlexLMLicenseServer):
    """
    Do the commands for invoking the license server have the correct data?
    """
    commands_list = flexlm_server.get_commands_list()
    assert commands_list == [
        [
            f"{settings.LMUTIL_PATH}",
            "lmstat",
            "-c",
            "2345@127.0.0.1",
            "-f",
        ]
    ]


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.flexlm.run_command")
async def test_flexlm_get_output_from_server(
    run_command_mock: mock.MagicMock,
    flexlm_server: FlexLMLicenseServer,
    lmstat_output: str,
):
    """
    Do the license server interface return the output from the license server?
    """
    run_command_mock.return_value = lmstat_output

    output = await flexlm_server.get_output_from_server("testproduct.testfeature")
    assert output == lmstat_output


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.flexlm.FlexLMLicenseServer.get_output_from_server")
async def test_flexlm_get_report_item(
    get_output_from_server_mock: mock.MagicMock, flexlm_server: FlexLMLicenseServer, lmstat_output: str
):
    """
    Do the FlexLM server interface generate a report item for the product?
    """
    get_output_from_server_mock.return_value = lmstat_output

    assert await flexlm_server.get_report_item("testproduct.testfeature") == LicenseReportItem(
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
@mock.patch("lm_agent.server_interfaces.flexlm.FlexLMLicenseServer.get_output_from_server")
async def test_flexlm_get_report_item_with_bad_output(
    get_output_from_server_mock: mock.MagicMock, flexlm_server: FlexLMLicenseServer, lmstat_output_bad: str
):
    """
    Do the FlexLM server interface raise an exception when the server returns an unparseable output?
    """
    get_output_from_server_mock.return_value = lmstat_output_bad

    with raises(LicenseManagerBadServerOutput):
        await flexlm_server.get_report_item("testproduct.testfeature")


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.flexlm.FlexLMLicenseServer.get_output_from_server")
async def test_flexlm_get_report_item_with_no_used_licenses(
    get_output_from_server_mock: mock.MagicMock,
    flexlm_server: FlexLMLicenseServer,
    lmstat_output_no_licenses: str,
):
    """
    Do the FlexLM server interface generate a report item when no licenses are in use?
    """
    get_output_from_server_mock.return_value = lmstat_output_no_licenses

    assert await flexlm_server.get_report_item("testproduct.testfeature") == LicenseReportItem(
        product_feature="testproduct.testfeature",
        used=0,
        total=1000,
        used_licenses=[],
    )
