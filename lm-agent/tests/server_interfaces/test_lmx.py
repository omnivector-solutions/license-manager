"""Test the LS-Dyna license server interface."""
from unittest import mock

from pytest import fixture, mark, raises

from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBadServerOutput
from lm_agent.server_interfaces.license_server_interface import LicenseReportItem
from lm_agent.server_interfaces.lmx import LMXLicenseServer


@fixture
def lmx_server(one_configuration_row_lmx) -> LMXLicenseServer:
    return LMXLicenseServer(one_configuration_row_lmx.license_servers)


def test_get_lmx_commands_list(lmx_server: LMXLicenseServer):
    """
    Do the commands for invoking the license server have the correct data?
    """
    commands_list = lmx_server.get_commands_list()
    assert commands_list == [
        [
            f"{settings.LMXENDUTIL_PATH}",
            "-licstat",
            "-host",
            "127.0.0.1",
            "-port",
            "2345",
        ]
    ]


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.lmx.run_command")
async def test_lmx_get_output_from_server(
    run_command_mock: mock.MagicMock,
    lmx_server: LMXLicenseServer,
    lmx_output: str,
):
    """
    Do the license server interface return the output from the license server?
    """
    run_command_mock.return_value = lmx_output

    output = await lmx_server.get_output_from_server()
    assert output == lmx_output


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.lmx.LMXLicenseServer.get_output_from_server")
async def test_lmx_get_report_item(
    get_output_from_server_mock: mock.MagicMock, lmx_server: LMXLicenseServer, lmx_output: str
):
    """
    Do the LM-X server interface generate a report item for the product?
    """
    get_output_from_server_mock.return_value = lmx_output

    assert await lmx_server.get_report_item(1, "hyperworks.hyperworks") == LicenseReportItem(
        feature_id=1,
        product_feature="hyperworks.hyperworks",
        used=25000,
        total=1000000,
        uses=[
            {"username": "sssaah", "lead_host": "RD0082406", "booked": 25000},
        ],
    )


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.lmx.LMXLicenseServer.get_output_from_server")
async def test_lmx_get_report_item_with_bad_output(
    get_output_from_server_mock: mock.MagicMock, lmx_server: LMXLicenseServer, lmx_output_bad: str
):
    """
    Do the LM-X server interface raise an exception when the server returns an unparseable output?
    """
    get_output_from_server_mock.return_value = lmx_output_bad

    with raises(LicenseManagerBadServerOutput):
        await lmx_server.get_report_item(1, "hyperworks.hyperworks")


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.lmx.LMXLicenseServer.get_output_from_server")
async def test_lmx_get_report_item_with_no_used_licenses(
    get_output_from_server_mock: mock.MagicMock,
    lmx_server: LMXLicenseServer,
    lmx_output_no_licenses: str,
):
    """
    Do the LM-X server interface generate a report item when no licenses are in use?
    """
    get_output_from_server_mock.return_value = lmx_output_no_licenses

    assert await lmx_server.get_report_item(1, "hyperworks.hyperworks") == LicenseReportItem(
        feature_id=1,
        product_feature="hyperworks.hyperworks",
        used=0,
        total=1000000,
        used_licenses=[],
    )
