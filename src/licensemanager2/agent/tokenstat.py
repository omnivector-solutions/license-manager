"""
Invoke license stat tools to build a view of license token counts
"""
import asyncio
from pathlib import Path
from shlex import quote
import typing

from pydantic import BaseModel, Field

from licensemanager2.agent import logger
from licensemanager2.agent.parsing import flexlm
from licensemanager2.agent.settings import SETTINGS


PRODUCT_FEATURE_RX = r"^.+?\..+$"
ENCODING = "UTF8"


class LicenseReportItem(BaseModel):
    """
    An item in a LicenseReport, a count of tokens for one product/feature
    """

    tool_name: str
    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    used: int

    @classmethod
    def from_stdout(cls, parse_fn, tool_name, product_feature, stdout):
        """
        Create a LicenseReportItem by parsing the stdout from the program that produced it
        """
        parsed = parse_fn(stdout)
        used = sum(int(x["tokens"]) for x in parsed)
        return LicenseReportItem(
            tool_name=tool_name, product_feature=product_feature, used=used
        )


TOOL_TIMEOUT = 6  # seconds


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

    def cmd_list(self) -> typing.List[str]:
        """
        A list of the command lines to run this tool, 1 per service host:port combination
        """
        ret = []
        addrs = SETTINGS.SERVICE_ADDRS.services[self.name].hostports
        for host, port in addrs:
            cl = self.args.format(
                exe=quote(str(self.path)), host=quote(host), port=port
            )
            ret.append(cl)

        return ret


class ToolOptionsCollection:
    """
    Specifications for running tools to access the license servers
    """

    tools: dict = {
        "flexlm": ToolOptions(
            name="flexlm",
            path=Path(f"{SETTINGS.BIN_PATH}/lmstat"),
            args="{exe} -c {port}@{host} -f abaqus.abaqus",
            parse_fn=flexlm.parse,
        ),
        # "other_tool": ToolOptions(...)
    }


async def check_tool_ports(tool_options: ToolOptions):
    """
    Run one checker, trying each host:port combination in turn, 1 at a time, until one succeeds
    """
    commands = tool_options.cmd_list()
    for cmd in commands:
        logger.info(f"{tool_options.name}: {cmd}")
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )

        # block until a check at this host:port succeeds or fails
        stdout, _ = await asyncio.wait_for(proc.communicate(), TOOL_TIMEOUT)
        output = str(stdout, encoding=ENCODING)
        if proc.returncode == 0:
            return LicenseReportItem.from_stdout(
                parse_fn=tool_options.parse_fn,
                tool_name=tool_options.name,
                product_feature="PROD.FEAT",
                stdout=output,
            )

        else:
            logger.info(f"rc = {proc.returncode}!")
            logger.info(output)

    raise RuntimeError(f"None of the checks for {tool_options.name} succeeded")


async def report():
    """
    Get the stat counts using a license stat tool, then send a
    reconcile to the backend
    """
    tool_awaitables = []
    for k in ToolOptionsCollection.tools:
        options = ToolOptionsCollection.tools[k]
        tool_awaitables.append(check_tool_ports(options))

    # run all checkers in parallel
    results = await asyncio.gather(*tool_awaitables, return_exceptions=True)
    for res in results:
        if isinstance(res, RuntimeError):
            logger.error(res)
        else:
            print(res)
