"""Test the LS-Dyna license server interface."""
from unittest import mock

from pytest import fixture, mark, raises

from lm_agent.config import settings
from lm_agent.exceptions import CommandFailedToExecute, LicenseManagerBadServerOutput
from lm_agent.models import LicenseReportItem
from lm_agent.server_interfaces.lsdyna import LSDynaLicenseServer


@fixture
def lsdyna_server(one_configuration_row_lsdyna) -> LSDynaLicenseServer:
    return LSDynaLicenseServer(one_configuration_row_lsdyna.license_servers)


def test_get_lsdyna_commands_list(lsdyna_server: LSDynaLicenseServer):
    """
    Do the commands for invoking the license server have the correct data?
    """
    commands_list = lsdyna_server.get_commands_list()
    assert commands_list == [
        [
            f"{settings.LSDYNA_PATH}",
            "-s",
            "2345@127.0.0.1",
            "-R",
        ]
    ]


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

    assert await lsdyna_server.get_report_item(1, "mppdyna.mppdyna") == LicenseReportItem(
        feature_id=1,
        product_feature="mppdyna.mppdyna",
        used=440,
        total=500,
        uses=[
            {"username": "dvds3g", "lead_host": "n-c13.com", "booked": 80},
            {"username": "ssss1d", "lead_host": "n-c52.com", "booked": 80},
            {"username": "ssss1d", "lead_host": "n-c15.com", "booked": 80},
            {"username": "ywap0o", "lead_host": "n-c53.com", "booked": 80},
            {"username": "ywap0o", "lead_host": "n-c51.com", "booked": 80},
            {"username": "ndha1a", "lead_host": "n-c55.com", "booked": 40},
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
        await lsdyna_server.get_report_item(1, "mppdyna.mppdyna")


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

    assert await lsdyna_server.get_report_item(1, "mppdyna.mppdyna") == LicenseReportItem(
        feature_id=1,
        product_feature="mppdyna.mppdyna",
        used=0,
        total=500,
        used_licenses=[],
    )


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.lsdyna.run_command")
@mock.patch("lm_agent.server_interfaces.lsdyna.LSDynaLicenseServer.get_commands_list")
async def test_lsdyna_get_report_item_continues_on_exception(
    get_commands_list_mock: mock.MagicMock,
    run_command_mock: mock.MagicMock,
    lsdyna_server: LSDynaLicenseServer,
    lsdyna_output: str,
):
    """
    Do the LS-Dyna server interface check the next command if the previous one fails?
    """
    get_commands_list_mock.return_value = [
        [
            f"{settings.LSDYNA_PATH}",
            "-s",
            "2345@127.0.0.1",
            "-R",
        ],
        [
            f"{settings.LSDYNA_PATH}",
            "-s",
            "3456@127.0.0.1",
            "-R",
        ],
    ]

    run_command_mock.side_effect = [CommandFailedToExecute("Command failed for first server"), lsdyna_output]

    assert await lsdyna_server.get_report_item(1, "mppdyna.mppdyna") == LicenseReportItem(
        feature_id=1,
        product_feature="mppdyna.mppdyna",
        used=440,
        total=500,
        uses=[
            {"username": "dvds3g", "lead_host": "n-c13.com", "booked": 80},
            {"username": "ssss1d", "lead_host": "n-c52.com", "booked": 80},
            {"username": "ssss1d", "lead_host": "n-c15.com", "booked": 80},
            {"username": "ywap0o", "lead_host": "n-c53.com", "booked": 80},
            {"username": "ywap0o", "lead_host": "n-c51.com", "booked": 80},
            {"username": "ndha1a", "lead_host": "n-c55.com", "booked": 40},
        ],
    )
