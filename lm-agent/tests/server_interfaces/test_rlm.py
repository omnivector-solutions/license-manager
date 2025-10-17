"""
Test the RLM license server interface.
"""

from unittest import mock

from pytest import fixture, mark, raises

from lm_agent.config import settings
from lm_agent.exceptions import CommandFailedToExecute, LicenseManagerBadServerOutput
from lm_agent.models import LicenseReportItem
from lm_agent.server_interfaces.rlm import RLMLicenseServer


@fixture
def rlm_server(one_configuration_row_rlm) -> RLMLicenseServer:
    return RLMLicenseServer(one_configuration_row_rlm.license_servers)


def test_get_rlm_commands_list(rlm_server: RLMLicenseServer):
    """
    Do the commands for invoking the license server have the correct data?
    """
    commands_list = rlm_server.get_commands_list()
    assert commands_list == [
        [
            f"{settings.RLMUTIL_PATH}",
            "rlmstat",
            "-c",
            "2345@127.0.0.1",
            "-a",
            "-p",
        ]
    ]


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

    assert await rlm_server.get_report_item(1, "converge.converge_super") == LicenseReportItem(
        feature_id=1,
        product_feature="converge.converge_super",
        used=93,
        total=1000,
        uses=[
            {"username": "asdj13", "lead_host": "myserver.example.com", "booked": 29},
            {"username": "cddcp2", "lead_host": "myserver.example.com", "booked": 27},
            {"username": "asdj13", "lead_host": "myserver.example.com", "booked": 37},
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
        await rlm_server.get_report_item(1, "converge.converge_super")


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.rlm.RLMLicenseServer.get_output_from_server")
async def test_rlm_get_report_item_with_no_used_licenses(
    get_output_from_server_mock: mock.MagicMock, rlm_server: RLMLicenseServer, rlm_output_no_licenses: str
):
    """
    Do the RLM server interface generate a report item when no licenses are in use?
    """
    get_output_from_server_mock.return_value = rlm_output_no_licenses

    assert await rlm_server.get_report_item(1, "converge.converge_super") == LicenseReportItem(
        feature_id=1,
        product_feature="converge.converge_super",
        used=0,
        total=1000,
        used_licenses=[],
    )


@mark.asyncio
@mock.patch("lm_agent.server_interfaces.rlm.run_command")
@mock.patch("lm_agent.server_interfaces.rlm.RLMLicenseServer.get_commands_list")
async def test_rlm_get_report_item_continues_on_exception(
    get_commands_list_mock: mock.MagicMock,
    run_command_mock: mock.MagicMock,
    rlm_server: RLMLicenseServer,
    rlm_output: str,
):
    """
    Do the RLM server interface check the next command if the previous one fails?
    """
    get_commands_list_mock.return_value = [
        [
            f"{settings.RLMUTIL_PATH}",
            "rlmstat",
            "-c",
            "2345@127.0.0.1",
            "-a",
            "-p",
        ],
        [
            f"{settings.RLMUTIL_PATH}",
            "rlmstat",
            "-c",
            "3456@127.0.0.1",
            "-a",
            "-p",
        ],
    ]

    run_command_mock.side_effect = [CommandFailedToExecute("Command failed for first server"), rlm_output]

    assert await rlm_server.get_report_item(1, "converge.converge_super") == LicenseReportItem(
        feature_id=1,
        product_feature="converge.converge_super",
        used=93,
        total=1000,
        uses=[
            {"username": "asdj13", "lead_host": "myserver.example.com", "booked": 29},
            {"username": "cddcp2", "lead_host": "myserver.example.com", "booked": 27},
            {"username": "asdj13", "lead_host": "myserver.example.com", "booked": 37},
        ],
    )
