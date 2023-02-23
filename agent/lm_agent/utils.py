"""Provide utilities to be used by interfaces."""
import asyncio
import shlex
from typing import List

from lm_agent.config import ENCODING, TOOL_TIMEOUT
from lm_agent.exceptions import CommandFailedToExecute
from lm_agent.logs import logger


async def run_command(command_line_parts: List[str]) -> str:
    """
    Run a command using a subprocess shell.
    Returns the output as string if the command succeeds.
    Raises CommandFailedToExecute exception if return code is not zero.
    """

    command_line = shlex.join(command_line_parts)
    proc = await asyncio.create_subprocess_shell(
        command_line, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )

    # block until the command succeeds
    stdout, _ = await asyncio.wait_for(proc.communicate(), TOOL_TIMEOUT)
    output = str(stdout, encoding=ENCODING)

    if proc.returncode != 0:
        error_message = shlex.join(
            [
                f"Command {command_line} failed!",
                f"Error: {output}",
                f"Return code: {proc.returncode}",
            ]
        )
        logger.error(error_message)
        raise CommandFailedToExecute(f"The command failed to execute, with return code {proc.returncode}.")

    return output
