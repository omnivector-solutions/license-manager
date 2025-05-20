"""Test the DSLS license server interface."""
from unittest import mock

from pytest import fixture, mark, raises

from lm_agent.config import settings
from lm_agent.exceptions import CommandFailedToExecute, LicenseManagerBadServerOutput
from lm_agent.models import LicenseReportItem, LicenseUsesItem
from lm_agent.server_interfaces.dsls import DSLSLicenseServer


@fixture
def dsls_server(one_configuration_row_dsls) -> DSLSLicenseServer:
    return DSLSLicenseServer(one_configuration_row_dsls.license_servers)


def test_get_dsls_commands_list(dsls_server: DSLSLicenseServer):
    """
    Do the commands for invoking the license server have the correct data?
    """
    commands_list = dsls_server.get_commands_list()
    assert commands_list == [
        {
            "input": "connect 127.0.0.1 2345\ngetLicenseUsage -csv",
            "command": [f"{settings.DSLICSRV_PATH}", "-admin"],
        },
    ]


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.dsls.run_command")
async def test_dsls_get_output_from_server(
    run_command_mock: mock.MagicMock,
    dsls_server: DSLSLicenseServer,
    dsls_output: str,
):
    """
    Do the license server interface return the output from the license server?
    """
    run_command_mock.return_value = dsls_output

    output = await dsls_server.get_output_from_server()
    assert output == dsls_output


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.dsls.DSLSLicenseServer.get_output_from_server")
async def test_dsls_get_report_item(
    get_output_from_server_mock: mock.MagicMock, dsls_server: DSLSLicenseServer, dsls_output: str
):
    """
    Do the DSLS server interface generate a report item for the product?
    """
    get_output_from_server_mock.return_value = dsls_output

    assert await dsls_server.get_report_item(1, "powerflow.pw7") == LicenseReportItem(
        feature_id=1,
        product_feature="powerflow.pw7",
        used=2,
        total=2000,
        uses=[
            LicenseUsesItem(username="user_1", lead_host="nid001627", booked=2),
        ],
    )


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.dsls.DSLSLicenseServer.get_output_from_server")
async def test_dsls_get_report_item_with_bad_output(
    get_output_from_server_mock: mock.MagicMock, dsls_server: DSLSLicenseServer, dsls_output_bad: str
):
    """
    Do the DSLS server interface raise an exception when the server returns an unparseable output?
    """
    get_output_from_server_mock.return_value = dsls_output_bad

    with raises(LicenseManagerBadServerOutput):
        await dsls_server.get_report_item(1, "powerflow.pw7")


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.dsls.DSLSLicenseServer.get_output_from_server")
async def test_dsls_get_report_item_with_warning_message(
    get_output_from_server_mock: mock.MagicMock, dsls_server: DSLSLicenseServer, dsls_output_with_warning: str
):
    """
    Do the DSLS server interface parse the output when the warning line is present?
    """
    get_output_from_server_mock.return_value = dsls_output_with_warning

    assert await dsls_server.get_report_item(1, "powerflow.sru") == LicenseReportItem(
        feature_id=1,
        product_feature="powerflow.sru",
        used=493,
        total=2374,
        uses=[
            LicenseUsesItem(username="user_1", lead_host="nid001234", booked=493),
        ],
    )


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.dsls.DSLSLicenseServer.get_output_from_server")
async def test_dsls_get_report_item_with_no_used_licenses(
    get_output_from_server_mock: mock.MagicMock,
    dsls_server: DSLSLicenseServer,
    dsls_output_no_licenses: str,
):
    """
    Do the DSLSserver interface generate a report item when no licenses are in use?
    """
    get_output_from_server_mock.return_value = dsls_output_no_licenses

    assert await dsls_server.get_report_item(1, "powerflow.pw7") == LicenseReportItem(
        feature_id=1,
        product_feature="powerflow.pw7",
        used=0,
        total=2000,
        used_licenses=[],
    )


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.dsls.run_command")
@mock.patch("lm_agent.server_interfaces.dsls.DSLSLicenseServer.get_commands_list")
async def test_dsls_get_report_item_continues_on_exception(
    get_commands_list_mock: mock.MagicMock,
    run_command_mock: mock.MagicMock,
    dsls_server: DSLSLicenseServer,
    dsls_output: str,
):
    """
    Do the DSLS server interface check the next command if the previous one fails?
    """
    get_commands_list_mock.return_value = [
        {
            "input": "connect 127.0.0.1 2345\ngetLicenseUsage -csv",
            "command": [f"{settings.DSLICSRV_PATH}", "-admin"],
        },
        {
            "input": "connect 127.0.0.0 3456\ngetLicenseUsage -csv",
            "command": [f"{settings.DSLICSRV_PATH}", "-admin"],
        },
    ]
    run_command_mock.side_effect = [CommandFailedToExecute("Command failed for first server"), dsls_output]

    assert await dsls_server.get_report_item(1, "powerflow.pw7") == LicenseReportItem(
        feature_id=1,
        product_feature="powerflow.pw7",
        used=2,
        total=2000,
        uses=[
            LicenseUsesItem(username="user_1", lead_host="nid001627", booked=2),
        ],
    )
