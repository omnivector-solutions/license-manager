"""Test the LS-Dyna license server interface."""
from unittest import mock

from pytest import fixture, mark, raises

from lm_agent.backend_utils import BackendConfigurationRow
from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBadServerOutput
from lm_agent.server_interfaces.license_server_interface import LicenseReportItem
from lm_agent.server_interfaces.lsdyna import LSDynaLicenseServer


@fixture
def lsdyna_server(one_configuration_row_lsdyna: BackendConfigurationRow) -> LSDynaLicenseServer:
    return LSDynaLicenseServer(one_configuration_row_lsdyna.license_servers)


def test_get_lsdyna_commands_list(lsdyna_server: LSDynaLicenseServer):
    """
    Do the commands for invoking the license server have the correct data?
    """
    commands_list = lsdyna_server.get_commands_list()
    assert commands_list == [f"{settings.LSDYNA_PATH} -s 2345@127.0.0.1 -R"]


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.lsdyna.run_command")
async def test_lsdyna_get_output_from_server(
    run_command_mock: mock.MagicMock,
    lsdyna_server: LSDynaLicenseServer,
    lsdyna_output: str,
):
    """
    Do the license server interface return the output from the license server?
    """
    run_command_mock.return_value = lsdyna_output

    output = await lsdyna_server.get_output_from_server()
    assert output == lsdyna_output


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.lsdyna.LSDynaLicenseServer.get_output_from_server")
async def test_lsdyna_get_report_item(
    get_output_from_server_mock: mock.MagicMock, lsdyna_server: LSDynaLicenseServer, lsdyna_output: str
):
    """
    Do the LS-Dyna server interface generate a report item for the product?
    """
    get_output_from_server_mock.return_value = lsdyna_output

    assert await lsdyna_server.get_report_item("mppdyna.mppdyna") == LicenseReportItem(
        product_feature="mppdyna.mppdyna",
        used=440,
        total=500,
        used_licenses=[
            {"user_name": "fane8y", "lead_host": "n-c13.maas.rnd.com", "booked": 80},
            {"user_name": "ssskmj", "lead_host": "n-c52.maas.rnd.com", "booked": 80},
            {"user_name": "ssskmj", "lead_host": "n-c15.maas.rnd.com", "booked": 80},
            {"user_name": "ywazrn", "lead_host": "n-c53.maas.rnd.com", "booked": 80},
            {"user_name": "ywazrn", "lead_host": "n-c51.maas.rnd.com", "booked": 80},
            {"user_name": "ndhtw9", "lead_host": "n-c55.maas.rnd.com", "booked": 40},
        ],
    )


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.lsdyna.LSDynaLicenseServer.get_output_from_server")
async def test_lsdyna_get_report_item_with_bad_output(
    get_output_from_server_mock: mock.MagicMock, lsdyna_server: LSDynaLicenseServer, lsdyna_output_bad: str
):
    """
    Do the LS-Dyna server interface raise an exception when the server returns an unparseable output?
    """
    get_output_from_server_mock.return_value = lsdyna_output_bad

    with raises(LicenseManagerBadServerOutput):
        await lsdyna_server.get_report_item("mppdyna.mppdyna")


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.lsdyna.LSDynaLicenseServer.get_output_from_server")
async def test_lsdyna_get_report_item_with_no_used_licenses(
    get_output_from_server_mock: mock.MagicMock,
    lsdyna_server: LSDynaLicenseServer,
    lsdyna_output_no_licenses: str,
):
    """
    Do the LS-Dyna server interface generate a report item when no licenses are in use?
    """
    get_output_from_server_mock.return_value = lsdyna_output_no_licenses

    assert await lsdyna_server.get_report_item("mppdyna.mppdyna") == LicenseReportItem(
        product_feature="mppdyna.mppdyna",
        used=0,
        total=500,
        used_licenses=[],
    )
