"""Slurm reservation CRUD module."""
from typing import Union

from lm_agent.config import settings
from lm_agent.exceptions import CommandFailedToExecute, LicenseManagerReservationFailure
from lm_agent.logs import logger
from lm_agent.utils import run_command


async def scontrol_create_reservation(licenses: str, duration: str) -> bool:
    """
    Create the reservation for licenses with the specified duration.

    Duration format: [days-]hours:minutes:seconds
    Licenses format: foo.bar@server:123,foo.baz@server:234

    Returns True if the reservation was created successfully, otherwise returns False.
    """
    cmd = [
        str(settings.SCONTROL_PATH),
        "create",
        "reservation",
        f"user={settings.LM_USER}",
        f"reservation={settings.RESERVATION_IDENTIFIER}",
        "starttime=now",
        f"duration={duration}",
        "flags=license_only",
        f"licenses={licenses}",
    ]

    logger.debug(f"#### Creating reservation for {licenses} with duration {duration} ####")
    try:
        await run_command(cmd)
    except CommandFailedToExecute:
        logger.error(f"#### Failed to create reservation {settings.RESERVATION_IDENTIFIER} ####")
        return False

    logger.debug(f"#### Successfully created reservation {settings.RESERVATION_IDENTIFIER} ####")
    return True


async def scontrol_show_reservation() -> Union[str, bool]:
    """
    Read reservation from the cluster.

    Returns the reservation information if it exists, otherwise returns None.
    """
    cmd = [
        str(settings.SCONTROL_PATH),
        "show",
        "reservation",
        settings.RESERVATION_IDENTIFIER,
    ]

    logger.debug(f"#### Getting reservation {settings.RESERVATION_IDENTIFIER} ####")
    try:
        reservation_output = await run_command(cmd)
    except CommandFailedToExecute:
        logger.error(f"#### Failed to read reservation {settings.RESERVATION_IDENTIFIER} ####")
        return False

    logger.debug(f"#### Successfully read reservation {settings.RESERVATION_IDENTIFIER} ####")
    return reservation_output


async def scontrol_update_reservation(licenses: str, duration: str) -> bool:
    """
    Update reservation duration and licenses.

    Duration format: [days-]hours:minutes:seconds
    Licenses format: foo.bar@server:123,foo.baz@server:234

    Returns True if the reservation was updated successfully, otherwise returns False.
    """
    cmd = [
        str(settings.SCONTROL_PATH),
        "update",
        "reservation",
        f"ReservationName={settings.RESERVATION_IDENTIFIER}",
        f"duration={duration}",
        f"licenses={licenses}",
    ]

    logger.debug(f"#### Updating reservation {settings.RESERVATION_IDENTIFIER} ####")
    try:
        await run_command(cmd)
    except CommandFailedToExecute:
        logger.error(f"#### Failed to update reservation {settings.RESERVATION_IDENTIFIER} ####")
        return False

    logger.debug(f"#### Successfully updated reservation {settings.RESERVATION_IDENTIFIER} ####")
    return True


async def scontrol_delete_reservation() -> bool:
    """
    Delete reservation.

    Returns True if the reservation was deleted successfully, otherwise returns False.
    """
    cmd = [
        str(settings.SCONTROL_PATH),
        "delete",
        f"ReservationName={settings.RESERVATION_IDENTIFIER}",
    ]

    logger.debug(f"#### Deleting reservation {settings.RESERVATION_IDENTIFIER} ####")
    try:
        await run_command(cmd)
    except CommandFailedToExecute:
        logger.error(f"#### Failed to delete reservation {settings.RESERVATION_IDENTIFIER} ####")
        return False

    logger.debug(f"#### Successfully deleted reservation {settings.RESERVATION_IDENTIFIER} ####")
    return True


async def create_or_update_reservation(reservation_data: str):
    """
    Create the reservation if it doesn't exist, otherwise update it.
    If the reservation cannot be updated, delete it and create a new one.
    """
    reservation = await scontrol_show_reservation()

    if reservation:
        updated = await scontrol_update_reservation(reservation_data, "30:00")
        if not updated:
            deleted = await scontrol_delete_reservation()
            LicenseManagerReservationFailure.require_condition(
                deleted, "Could not update or delete reservation."
            )
    else:
        created = await scontrol_create_reservation(reservation_data, "30:00")
        LicenseManagerReservationFailure.require_condition(created, "Could not create reservation.")
