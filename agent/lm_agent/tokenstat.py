"""
Invoke license stat tools to build a view of license token counts
"""
import asyncio
import re
import traceback
import typing
from pathlib import Path
from shlex import quote

from pydantic import BaseModel, Field

from lm_agent.backend_utils import BackendConfigurationRow, get_config_from_backend
from lm_agent.config import ENCODING, PRODUCT_FEATURE_RX, TOOL_TIMEOUT, settings
from lm_agent.logs import logger
from lm_agent.parsing import flexlm, rlm
from lm_agent.workload_managers.slurm.cmd_utils import scontrol_show_lic


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


def _filter_current_feature(parsed_list, feature):
    """
    Get the current feature from the parsed list.
    """
    for feature_item in parsed_list:
        if feature_item["feature"].count("_") == 0:  # `converge`
            if feature_item["feature"] == feature:
                return feature_item
        elif "".join(feature_item["feature"].split("_")[1:]) == feature:
            # `converge_super` | `converge_gui_polygonica` | `converge_...`
            return feature_item


def _filter_used_features(parsed_list, feature):
    used_licenses = []
    for feature_booked in parsed_list:
        if feature_booked["feature"].count("_") == 0:
            if feature_booked["feature"] == feature:
                used_licenses.append(feature_booked)
        elif "".join(feature_booked["feature"].split("_")[1:]) == feature:
            used_licenses.append(feature_booked)
    return used_licenses


def _cleanup_features(features_list):
    """
    Remove the feature key for each entry in the parsed["uses"], since we already handled it.
    """
    for feature in features_list:
        del feature["feature"]
    return features_list


class RLMReportItem(BaseModel):
    """
    An item in a RLM report, a count of tokens for one product/feature.
    """

    tool_name: str
    product_feature: str
    used: int
    total: int
    used_licenses: typing.List

    @classmethod
    def from_stdout(cls, product, parse_fn, tool_name, stdout):
        """Create a RLM by parsing the stdout from the program that produced it."""
        parsed = parse_fn(stdout)
        product, feature = product.split("_")[0], "_".join(product.split("_")[1:])
        if not feature:
            feature = product
        current_feature_item = _filter_current_feature(parsed["total"], feature)
        feature_booked_licenses = _filter_used_features(parsed["uses"], feature)
        used_licenses = _cleanup_features(feature_booked_licenses)
        return cls(
            tool_name=tool_name,
            product_feature=f"{product}.{feature}",
            used=current_feature_item["used"],
            total=current_feature_item["total"],
            used_licenses=used_licenses,
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
        "rlm": ToolOptions(
            name="rlm",
            path=Path(f"{settings.BIN_PATH}/rlmstat"),
            args="{exe} -c {port}@{host} -a -p",
            parse_fn=rlm.parse,
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

        if proc.returncode != 0:
            logger.error(f"Error: {output} | Return Code: {proc.returncode}")
            raise RuntimeError(f"None of the checks for {tool_options.name} succeeded")

        if tool_options.name == "flexlm":
            lri = LicenseReportItem.from_stdout(
                parse_fn=tool_options.parse_fn,
                tool_name=tool_options.name,
                product=product,
                stdout=output,
            )
        elif tool_options.name == "rlm":
            lri = RLMReportItem.from_stdout(
                parse_fn=tool_options.parse_fn,
                tool_name=tool_options.name,
                product=f"{product}_{feature}",
                stdout=output,
            )

        return lri


def get_all_product_features_from_cluster(show_lic_output: str) -> typing.List[str]:
    """
    Returns a list of all product.feature in the cluster
    """
    PRODUCT_FEATURE = r"LicenseName=(?P<product>[a-zA-Z0-9_]+)[_\-.](?P<feature>\w+)"
    RX_PRODUCT_FEATURE = re.compile(PRODUCT_FEATURE)

    parsed_features = []
    output = show_lic_output.split("\n")
    for line in output:
        parsed_line = RX_PRODUCT_FEATURE.match(line)
        if parsed_line:
            parsed_data = parsed_line.groupdict()
            product = parsed_data["product"]
            feature = parsed_data["feature"]
            parsed_features.append(f"{product}.{feature}")

    return parsed_features


def get_local_license_configurations(
    license_configurations: typing.List[BackendConfigurationRow], local_licenses: typing.List[str]
) -> typing.List[BackendConfigurationRow]:
    """
    Return the license configurations from the backend that are configured on the cluster.
    """
    filtered_entries = []

    for entry in license_configurations:
        for feature in entry.features.keys():
            if f"{entry.product}.{feature}" in local_licenses:
                filtered_entries.append(entry)
                continue
    return filtered_entries


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
    license_configurations = await get_config_from_backend()
    local_licenses = get_all_product_features_from_cluster(await scontrol_show_lic())
    filtered_entries = get_local_license_configurations(license_configurations, local_licenses)

    for entry in filtered_entries:
        for license_server_type in tools:
            if entry.license_server_type == license_server_type:
                options = tools[license_server_type]
                for feature in entry.features.keys():
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
