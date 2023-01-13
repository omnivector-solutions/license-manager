"""Slurm reservation interface."""
import asyncio
import shlex

from lm_agent.config import RESERVATION_IDENTIFIER
from lm_agent.logs import logger
from lm_agent.utils import run_command
from lm_agent.workload_managers.slurm.common import CMD_TIMEOUT, SCONTROL_PATH


async def scontrol_create_reservation(licenses: str, duration: str) -> bool:
    """
    Create the reservation for licenses with the specified duration.

    Duration format: [days-]hours:minutes:seconds
    Licenses format: foo.bar@server:123,foo.baz@server:234

    Returns True if the reservation was created successfully, otherwise returns False.
    """
    cmd = [
        SCONTROL_PATH,
        "create",
        "reservation",
        "user=license-manager",
        f"reservation={RESERVATION_IDENTIFIER}",
        "starttime=now",
        f"duration={duration}",
        "flags=license_only",
        f"licenses={licenses}",
    ]

    logger.debug(f"#### Creating reservation for {licenses} with duration {duration} ####")
    reservation_output = await run_command(shlex.join(cmd))

    if not reservation_output or f"Reservation created: {RESERVATION_IDENTIFIER}" not in reservation_output:
        logger.error(f"#### Failed to create reservation ####")
        return False

    logger.debug(f"#### Successfully created reservation ####")
    return True


    if return_code != 0:
        logger.error(
            f"#### Failed to create reservation"
            f"return code: {return_code}"
            f"stdout: {reservation_create_stdout} ####"
        )
        return False

    logger.debug(f"#### Successfully created reservation ####")

    return True


async def scontrol_update_reservation(licenses: str, duration: str) -> bool:
    """
    Update reservation duration and licenses.

    Duration format: [days-]hours:minutes:seconds
    Licenses format: foo.bar@server:123,foo.baz@server:234

    Returns True if the reservation was updated successfully, otherwise returns False.
    """
    cmd = [
        SCONTROL_PATH,
        "update",
        "reservation",
        f"ReservationName={RESERVATION_IDENTIFIER}",
        f"duration={duration}",
        f"licenses={licenses}",
    ]

    logger.debug(f"#### Updating reservation {RESERVATION_IDENTIFIER} ####")
    reservation_output = await run_command(shlex.join(cmd))

    if not reservation_output or "Reservation updated." not in reservation_output:
        logger.error(f"#### Failed to update reservation ####")
        return False

    logger.debug(f"#### Successfully updated reservation ####")

    return True


async def scontrol_delete_reservation() -> bool:
    """
    Delete reservation.

    Returns True if the reservation was deleted successfully, otherwise returns False.
    """
    cmd = [
        SCONTROL_PATH,
        "delete",
        "reservation",
        f"ReservationName={RESERVATION_IDENTIFIER}",
    ]

    logger.debug(f"#### Deleting reservation {RESERVATION_IDENTIFIER} ####")
    reservation_output = await run_command(shlex.join(cmd))

    # Reservation delete command doesn't output any message on success
    if reservation_output != "":
        logger.error(f"#### Failed to delete reservation ####")
        return False

    logger.debug(f"#### Successfully deleted reservation ####")

    return True
