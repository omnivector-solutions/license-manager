"""
Invoke license stat tools to build a view of license token counts
"""
import asyncio
import traceback
import typing
from pathlib import Path
from shlex import quote

from pydantic import BaseModel, Field

from lm_agent.backend_utils import get_config_from_backend
from lm_agent.config import ENCODING, PRODUCT_FEATURE_RX, TOOL_TIMEOUT, settings
from lm_agent.logs import logger
from lm_agent.parsing import flexlm


class LicenseService(BaseModel):
    """
    A license service such as "flexlm", with a set of host-port tuples
    representing the network location where the service is listening.
    """

    name: str
    hostports: typing.List[typing.Tuple[str, int]]


class LicenseReportItem(BaseModel):
    """
    An item in a LicenseReport, a count of tokens for one product/feature
    """

    tool_name: str
    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    used: int
    total: int
    used_licenses: typing.List

    @classmethod
    def from_stdout(cls, product, parse_fn, tool_name, stdout):
        """
        Create a LicenseReportItem by parsing the stdout from the program that
        produced it.
        """
        parsed = parse_fn(stdout)
        return cls(
            tool_name=tool_name,
            product_feature=f"{product}.{parsed['total']['feature']}",
            used=parsed["total"]["used"],
            total=parsed["total"]["total"],
            used_licenses=parsed["uses"],
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

    def cmd_list(self, license_servers: typing.List[str]) -> typing.List[str]:
        """
        A list of the command lines to run this tool, 1 per service host:port combination
        """

        host_ports = [(server.split(":")[1], server.split(":")[2]) for server in license_servers]
        ret = []
        for host, port in host_ports:
            cl = self.args.format(exe=quote(str(self.path)), host=quote(host), port=port)
            ret.append(cl)
        return ret


class ToolOptionsCollection:
    """
    Specifications for running tools to access the license servers
    """

    tools: typing.Dict[str, ToolOptions] = {
        "flexlm": ToolOptions(
            name="flexlm",
            path=Path(f"{settings.BIN_PATH}/lmstat"),
            args="{exe} -c {port}@{host} -f",
            parse_fn=flexlm.parse,
        ),
        # "other_tool": ToolOptions(...)
    }


async def attempt_tool_checks(
    tool_options: ToolOptions, product: str, feature: str, license_servers: typing.List[str]
):
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
                        attempt_tool_checks(options, entry.product, feature, entry.license_servers)
                    )
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
