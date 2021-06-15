"""
Invoke license stat tools to build a view of license token counts
"""
import asyncio
from pathlib import Path
from shlex import quote
import traceback
import typing

from pydantic import BaseModel, Field
from typing import List

from licensemanager2.agent import log as logger
from licensemanager2.agent.parsing import flexlm
from licensemanager2.agent.settings import (
    SETTINGS,
    PRODUCT_FEATURE_RX,
    ENCODING,
    TOOL_TIMEOUT
)

from licensemanager2.agent.backend_utils import get_config_from_backend

from licensemanager2.workload_managers.slurm.cmd_utils import (
    get_tokens_for_license,
    sacctmgr_modify_resource,
)


class LicenseService(BaseModel):
    """
    A license service such as "flexlm", with a set of host-port tuples
    representing the network location where the service is listening.
    """

    name: str
    hostports: typing.List[typing.Tuple[str, int]]


class LicenseServiceCollection(BaseModel):
    """
    A collection of LicenseServices, mapped by their names
    """

    services: typing.Dict[str, LicenseService]

    @classmethod
    def from_env_string(cls, env_str: str) -> "LicenseServiceCollection":
        """
        @returns LicenseServiceCollection from parsing colon-separated env input

        The syntax is:

        - servicename:host:port e.g. "flexlm:172.0.1.2:2345"

        - each entry separated by spaces e.g.
          "flexlm:172.0.1.2:2345 abclm:172.0.1.3:2319"

        - if the same service appears twice in the list they will be
          merged, e.g.:
          "flexlm:173.0.1.2:2345 flexlm:172.0.1.3:2345"
          -> (pseudodata) "flexlm": [("173.0.1.2", 2345), "173.0.1.3", 2345)]
        """
        self = cls(services={})
        services = env_str.split()
        for item in services:
            name, host, port = item.split(":", 2)

            svc = self.services.setdefault(
                name, LicenseService(name=name, hostports=[])
            )
            svc.hostports.append((host, int(port)))

        return self


class LicenseReportItem(BaseModel):
    """
    An item in a LicenseReport, a count of tokens for one product/feature
    """

    tool_name: str
    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    used: int
    total: int

    @classmethod
    def from_stdout(cls, product, parse_fn, tool_name, stdout):
        """
        Create a LicenseReportItem by parsing the stdout from the program that
        produced it.
        """
        parsed = parse_fn(stdout)
        return cls(
            tool_name=tool_name,
            product_feature=f"{product}.{parsed['feature']}",
            used=parsed["used"],
            total=parsed["total"],
        )


class ToolOptions(BaseModel):
    """
    Specifications for running one of the tools that accesses license servers
    """

    name: str
    path: Path
    args: str
    # This runs into https://github.com/python/mypy/issues/708 if we try to specify the argument
    # types. this is because parse_fn *looks like* a method when it's an attribute of this class;
    # but in fact it is (usually) a simple function. As a workaround, the argument types are
    # unspecified, but it should be `[str]`
    parse_fn: typing.Callable[..., typing.List[dict]]

    def cmd_list(self, license_servers) -> typing.List[str]:
        """
        A list of the command lines to run this tool, 1 per service host:port combination
        """

        host_ports = [
            (server.split(":")[1], server.split(":")[2])
            for server in license_servers
        ]
        ret = []
        for host, port in host_ports:
            cl = self.args.format(
                exe=quote(str(self.path)), host=quote(host), port=port
            )
            ret.append(cl)
        return ret


class ToolOptionsCollection:
    """
    Specifications for running tools to access the license servers
    """

    tools: typing.Dict[str, ToolOptions] = {
        "flexlm": ToolOptions(
            name="flexlm",
            path=Path(f"{SETTINGS.BIN_PATH}/lmstat"),
            args="{exe} -c {port}@{host} -f",
            parse_fn=flexlm.parse,
        ),
        # "other_tool": ToolOptions(...)
    }


async def attempt_tool_checks(
        tool_options: ToolOptions, product: str, feature: str, license_servers: List[str]):
    """
    Run one checker tool, attempting each host:port combination in turn, 1 at
    a time, until one succeeds.
    """
    # NOTE: Only pass the feature into this function as a temporary workaround
    # until we fix the ToolOptions to somehow support setting the feature.

    commands = tool_options.cmd_list(license_servers)
    for cmd in commands:
        # NOTE: find a better way to get the feature into the command.
        cmd = cmd + f" {feature}"
        logger.info(f"{tool_options.name}: {cmd}")
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )

        # block until a check at this host:port succeeds or fails
        stdout, _ = await asyncio.wait_for(proc.communicate(), TOOL_TIMEOUT)
        output = str(stdout, encoding=ENCODING)

        if proc.returncode == 0:
            lri = LicenseReportItem.from_stdout(
                parse_fn=tool_options.parse_fn,
                tool_name=tool_options.name,
                product=product,
                stdout=output,
            )

            # Account for used slurm tokens
            #
            # License represented in format
            #    <product>.<feature>@<license_server>
            slurm_license = f"{product}.{feature}@{tool_options.name}"

            # Get the used licenses from the scontrol output
            slurm_used = await get_tokens_for_license(slurm_license, "Used")

            # If slurm is already tracking the license, update slurmdbd
            # with a modified view of the total licenses.
            #
            # To give slurm a more accurate view of the number of tokens
            # in use vs the number available, we add the number of tokens in
            # use by slurm to the number of available tokens returned from
            # the license server.
            if slurm_used is None:
                slurm_used = 0

            # Generate the new total including the used tokens for slurm
            slurm_available = lri.total - lri.used + slurm_used

            # Update slurmdbd with the modified accounting
            update_resource = await sacctmgr_modify_resource(
                product, feature, slurm_available
            )
            if update_resource:
                logger.info("Slurmdbd updated successfully.")
            else:
                logger.info("Slurmdbd update unsuccessful.")

            return lri

        else:
            logger.warning(f"rc = {proc.returncode}!")
            logger.warning(output)

    raise RuntimeError(f"None of the checks for {tool_options.name} succeeded")


async def report() -> typing.List[dict]:
    """
    Get stat counts using a license stat tool

    This function iterates over the available license_servers and associated
    features configured via LICENSE_SERVER_FEATURES and generates
    a report by requesting license information from the license_server_type.

    The return from the license server is used to reconcile license-manager's
    view of what features are available with what actually exists in the
    license server database.
    """
    tool_awaitables = []
    reconciliation = []
    tools = ToolOptionsCollection.tools

    # Iterate over the license servers and features appending to list
    # of tools/cmds to be ran.
    entries = await get_config_from_backend()
    for entry in entries:
        for license_server_type in tools:
            if entry.license_server_type == license_server_type:
                options = tools[license_server_type]
                for feature in entry.features:
                    tool_awaitables.append(
                        attempt_tool_checks(
                            options,
                            entry.product,
                            feature,
                            entry.license_servers
                        )
                    )
    if entries:
        print("hello   " + entries[0].license_server_type + " " + entries[0].features[0])
        print(tool_awaitables)
    # run all checkers in parallel
    results = await asyncio.gather(*tool_awaitables, return_exceptions=True)
    for res in results:
        if isinstance(res, Exception):
            formatted = traceback.format_exception(type(res), res, res.__traceback__)
            logger.error("".join(formatted))
        else:
            rec_item = res.dict(exclude={"tool_name"})
            reconciliation.append(rec_item)

    return reconciliation