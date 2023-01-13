"""Slurm reservation interface."""
import asyncio
import shlex

from lm_agent.config import RESERVATION_IDENTIFIER
from lm_agent.logs import logger
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

    logger.debug(f"#### Creating reservation with command: {' '.join(cmd)} ####")

    reservation_create_resource = await asyncio.create_subprocess_shell(
        shlex.join(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    reservation_create_stdout, _ = await asyncio.wait_for(
        reservation_create_resource.communicate(),
        CMD_TIMEOUT,
    )

    return_code = reservation_create_resource.return_code

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

    logger.debug(f"#### Updating reservation {RESERVATION_IDENTIFIER} with command: {' '.join(cmd)} ####")

    reservation_update_resource = await asyncio.create_subprocess_shell(
        shlex.join(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    reservation_update_stdout, _ = await asyncio.wait_for(
        reservation_create_resource.communicate(),
        CMD_TIMEOUT,
    )

    return_code = reservation_update_resource.return_code

    if return_code != 0:
        logger.error(
            f"#### Failed to update reservation"
            f"return code: {return_code}"
            f"stdout: {reservation_update_stdout} ####"
        )
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

    reservation_delete_resource = await asyncio.create_subprocess_shell(
        shlex.join(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    reservation_delete_stdout, _ = await asyncio.wait_for(
        reservation_delete_resource.communicate(),
        CMD_TIMEOUT,
    )

    return_code = reservation_delete_resource.return_code

    if return_code != 0:
        logger.error(
            f"#### Failed to delete reservation"
            f"return code: {return_code}"
            f"stdout: {reservation_delete_stdout} ####"
        )
        return False

    logger.debug(f"#### Successfully deleted reservation ####")

    return True
