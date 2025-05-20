"""Provide utilities to be used by interfaces."""
import asyncio
import shlex
from typing import List, Optional

from lm_agent.config import settings
from lm_agent.exceptions import CommandFailedToExecute
from lm_agent.logs import logger


async def run_command(command_line_parts: List[str], stdin_str: Optional[str] = "") -> str:
    """
    Run a command using a subprocess shell.

    The command is passed as a list of strings, where each string is a part of the command.
    You can also provide a string to be passed as stdin to the process.

    Returns the output as string if the command succeeds.
    Raises CommandFailedToExecute exception if return code is not zero.
    """

    command_line = shlex.join(command_line_parts)
    stdin_bytes = stdin_str.encode(settings.ENCODING) if stdin_str else None

    proc = await asyncio.create_subprocess_shell(
        command_line,
        stdin=asyncio.subprocess.PIPE if stdin_bytes else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(stdin_bytes), settings.TOOL_TIMEOUT)
        output = str(stdout, encoding=settings.ENCODING, errors="replace")

        if proc.returncode != 0:
            error_message = shlex.join(
                [
                    f"Command {command_line} failed!",
                    f"Error: {output}",
                    f"Return code: {proc.returncode}",
                ]
            )
            logger.error(error_message)
            raise CommandFailedToExecute(
                f"The command failed to execute, with return code {proc.returncode}."
            )
    except asyncio.TimeoutError:
        logger.error(f"Command {command_line} timed out after {settings.TOOL_TIMEOUT} seconds.")
        raise CommandFailedToExecute(
            f"The command failed to execute, timed out after {settings.TOOL_TIMEOUT} seconds."
        )

    return output
