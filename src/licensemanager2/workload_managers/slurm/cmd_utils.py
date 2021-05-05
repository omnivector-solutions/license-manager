"""Utilities that interact with slurm."""
import asyncio
import re
import shlex

from typing import Optional

from licensemanager2.agent import log as logger


def get_used_tokens_for_license(
        product_feature_server: str,
        scontrol_output: str
) -> Optional[int]:
    """
    Return used tokens from scontrol output.
    """

    def match_product_feature_server() -> Optional[str]:
        """
        Return the line after the matched product_feature line.
        """
        matched = False
        for line in scontrol_output.split("\n"):
            if matched:
                return line
            if len(re.findall(rf"({product_feature_server})", line)) > 0:
                matched = True
        return None

    token_str = match_product_feature_server()
    if token_str is not None:
        for item in token_str.split():
            k, v = item.split("=")
            if k == "Used":
                return int(v)
    return None


async def scontrol_show_lic():
    """
    Get the license usage from scontrol.
    """

    cmd = "/usr/bin/scontrol show lic"
    timeout = 5
    encoding = "UTF8"

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    stdout, _ = await asyncio.wait_for(proc.communicate(), timeout)
    output = str(stdout, encoding=encoding)
    return output


async def sacctmgr_modify_resource(product: str, feature: str, num_tokens):
    """
    Update the license resource in slurm.
    """
    cmd = [
        "/usr/bin/sacctmgr",
        "modify",
        "resource",
        f"name={product}.{feature}",
        "set",
        f"count={num_tokens}",
        "-i",
    ]
    timeout = 5
    encoding = "UTF8"

    logger.info(f"{' '.join(cmd)}")

    sacctmgr_modify_resource = await asyncio.create_subprocess_shell(
        shlex.join(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    modify_resource_stdout, _ = await asyncio.wait_for(
        sacctmgr_modify_resource.communicate(),
        timeout,
    )

    rc = sacctmgr_modify_resource.returncode

    if not rc == 0:
        logger.warning(f"rc = {rc}!")
        logger.warning(modify_resource_stdout)

    modify_resource_output = str(modify_resource_stdout, encoding=encoding)
    logger.info(f"Slurmdbd updated successfully: {modify_resource_output}")
