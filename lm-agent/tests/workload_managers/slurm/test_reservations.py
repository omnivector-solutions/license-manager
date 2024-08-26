"""
Test Slurm reservations.
"""
from unittest import mock

from pytest import fixture, mark

from lm_agent.config import settings
from lm_agent.exceptions import CommandFailedToExecute
from lm_agent.workload_managers.slurm.reservations import (
    scontrol_create_reservation,
    scontrol_delete_reservation,
    scontrol_show_reservation,
    scontrol_update_reservation,
    create_or_update_reservation,
)


@fixture
def reservation_license_data():
    return "test.license@licenseserver:10,another.license@server:25"


@fixture
def reservation_duration():
    return "24:00:00"


@fixture
def reservation_show_output():
    return """
    ReservationName=license-manager-reservation StartTime=2023-01-11T02:38:16 EndTime=2023-01-12T02:38:16 Duration=24:00:00
    Nodes=(null) NodeCnt=0 CoreCnt=0 Features=(null) PartitionName=(null) Flags=ANY_NODES
    TRES=(null)
    Users=license-manager Groups=(null) Accounts=(null) Licenses=test.license@licenseserver:10,another.license@server:25 State=ACTIVE BurstBuffer=(null) Watts=n/a
    MaxStartDelay=(null)
    """


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.reservations.run_command")
async def test__scontrol_create_reservation__success(
    run_command_mock: mock.MagicMock, reservation_license_data, reservation_duration
):
    """Test if a reservation is created succesfully."""
    run_command_mock.return_value = f"Reservation created: {settings.RESERVATION_IDENTIFIER}"
    create_reservation = await scontrol_create_reservation(reservation_license_data, reservation_duration)
    assert create_reservation


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.reservations.run_command")
async def test__scontrol_create_reservation__fail(
    run_command_mock: mock.MagicMock, reservation_license_data, reservation_duration
):
    """Test if reservation creation fails when the command fails or the reservation is invalid."""
    run_command_mock.side_effect = CommandFailedToExecute("Command failed")
    create_reservation = await scontrol_create_reservation(reservation_license_data, reservation_duration)
    assert not create_reservation


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.reservations.run_command")
async def test__scontrol_show_reservation__success(run_command_mock: mock.MagicMock, reservation_show_output):
    """Test if reservation is fetched succesfully."""
    run_command_mock.return_value = reservation_show_output
    read_reservation = await scontrol_show_reservation()
    assert read_reservation == reservation_show_output


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.reservations.run_command")
async def test__scontrol_show_reservation__fail(run_command_mock: mock.MagicMock):
    """Test if reservation fetch fails when the command fails or the reservation is not found."""
    run_command_mock.side_effect = CommandFailedToExecute("Command failed")
    read_reservation = await scontrol_show_reservation()
    assert not read_reservation


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.reservations.run_command")
async def test__scontrol_update_reservation__success(
    run_command_mock: mock.MagicMock, reservation_license_data, reservation_duration
):
    """Test if reservation is updated succesfully."""
    run_command_mock.return_value = "Reservation updated."
    update_reservation = await scontrol_update_reservation(reservation_license_data, reservation_duration)
    assert update_reservation


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.reservations.run_command")
async def test__scontrol_update_reservation__fail(
    run_command_mock: mock.MagicMock, reservation_license_data, reservation_duration
):
    """Test if reservation update fails when the command fails or the reservation is invalid."""
    run_command_mock.side_effect = CommandFailedToExecute("Command failed")
    update_reservation = await scontrol_update_reservation(reservation_license_data, reservation_duration)
    assert not update_reservation


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.reservations.run_command")
async def test__scontrol_delete_reservation__success(run_command_mock: mock.MagicMock):
    """Test if reservation is deleted succesfully."""
    run_command_mock.return_value = ""
    delete_reservation = await scontrol_delete_reservation()
    assert delete_reservation


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.reservations.run_command")
async def test__scontrol_delete_reservation__fail(run_command_mock: mock.MagicMock):
    """Test if reservation deletion fails when the command fails or the reservation is invalid."""
    run_command_mock.side_effect = CommandFailedToExecute("Command failed")
    delete_reservation = await scontrol_delete_reservation()
    assert not delete_reservation


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.reservations.scontrol_create_reservation")
@mock.patch("lm_agent.workload_managers.slurm.reservations.scontrol_show_reservation")
@mock.patch("lm_agent.workload_managers.slurm.reservations.scontrol_update_reservation")
@mock.patch("lm_agent.workload_managers.slurm.reservations.scontrol_delete_reservation")
async def test_create_or_update_reservation(delete_mock, update_mock, show_mock, create_mock):
    """
    Test that create_or_update_reservation:
    - update the reservation if it exists
    - delete the reservation if it can't update
    - create the reservation if doesn't exist
    """
    # Update reservation if it exists
    show_mock.return_value = "reservation_data"
    await create_or_update_reservation("reservation_info")
    update_mock.assert_called_once()

    # Delete reservation if it can't update
    show_mock.return_value = "reservation_data"
    update_mock.return_value = False
    await create_or_update_reservation("reservation_info")
    delete_mock.assert_called()

    # Create reservation if it doesn't exist
    show_mock.return_value = False
    await create_or_update_reservation("reservation_info")
    create_mock.assert_called()
