"""Test the OLicense license server interface."""
from unittest import mock

from pytest import fixture, mark, raises

from lm_agent.backend_utils import BackendConfigurationRow
from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBadServerOutput
from lm_agent.server_interfaces.license_server_interface import LicenseReportItem
from lm_agent.server_interfaces.olicense import OLicenseLicenseServer


@fixture
def olicense_server(one_configuration_row_olicense: BackendConfigurationRow) -> OLicenseLicenseServer:
    return OLicenseLicenseServer(one_configuration_row_olicense.license_servers)


def test_get_olicense_commands_list(olicense_server: OLicenseLicenseServer):
    """
    Do the commands for invoking the license server have the correct data?
    """
    commands_list = olicense_server.get_commands_list()
    assert commands_list == [f"{settings.OLIXTOOL_PATH} -sv 127.0.0.1:2345"]


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.olicense.run_command")
async def test_olicense_get_output_from_server(
    run_command_mock: mock.MagicMock,
    olicense_server: OLicenseLicenseServer,
    olicense_output: str,
):
    """
    Do the license server interface return the output from the license server?
    """
    run_command_mock.return_value = olicense_output

    output = await olicense_server.get_output_from_server()
    assert output == olicense_output


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.olicense.OLicenseLicenseServer.get_output_from_server")
async def test_olicense_get_report_item(
    get_output_from_server_mock: mock.MagicMock, olicense_server: OLicenseLicenseServer, olicense_output: str
):
    """
    Do the OLicense server interface generate a report item for the product?
    """
    get_output_from_server_mock.return_value = olicense_output

    assert await olicense_server.get_report_item("cosin.ftire_adams") == LicenseReportItem(
        product_feature="cosin.ftire_adams",
        used=3,
        total=4,
        used_licenses=[
            {"user_name": "sbhyma", "lead_host": "RD0087712", "booked": 1},
            {"user_name": "sbhyma", "lead_host": "RD0087713", "booked": 1},
            {"user_name": "user22", "lead_host": "RD0087713", "booked": 1},
        ],
    )


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.olicense.OLicenseLicenseServer.get_output_from_server")
async def test_olicense_get_report_item_with_bad_output(
    get_output_from_server_mock: mock.MagicMock, olicense_server: OLicenseLicenseServer, olicense_output_bad: str
):
    """
    Do the OLicense server interface raise an exception when the server returns an unparseable output?
    """
    get_output_from_server_mock.return_value = olicense_output_bad

    with raises(LicenseManagerBadServerOutput):
        await olicense_server.get_report_item("cosin.ftire_adams")


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.olicense.OLicenseLicenseServer.get_output_from_server")
async def test_lmx_get_report_item_with_no_used_licenses(
    get_output_from_server_mock: mock.MagicMock,
    olicense_server: OLicenseLicenseServer,
    olicense_output_no_licenses: str,
):
    """
    Do the OLicense server interface generate a report item when no licenses are in use?
    """
    get_output_from_server_mock.return_value = olicense_output_no_licenses

    assert await olicense_server.get_report_item("cosin.ftire_adams") == LicenseReportItem(
        product_feature="cosin.ftire_adams",
        used=0,
        total=4,
        used_licenses=[],
    )
