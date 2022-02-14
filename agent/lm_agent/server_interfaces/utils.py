"""Provide utilities to be used by some of the license server interfaces."""
import asyncio

from lm_agent.config import ENCODING, TOOL_TIMEOUT
from lm_agent.logs import logger


async def run_command(command_line: str):
    """Run a command using a subprocess shell."""

    proc = await asyncio.create_subprocess_shell(
        command_line, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )

    # block until the command succeeds
    stdout, _ = await asyncio.wait_for(proc.communicate(), TOOL_TIMEOUT)
    output = str(stdout, encoding=ENCODING)

    if proc.returncode != 0:
        logger.error(f"Error: {output} | Return Code: {proc.returncode}")
        return None
    return output
