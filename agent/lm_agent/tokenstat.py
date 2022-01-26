"""
Invoke license stat tools to build a view of license token counts.
"""
import abc
import asyncio
import re
import typing

from pydantic import BaseModel, Field

from lm_agent.backend_utils import BackendConfigurationRow, get_config_from_backend
from lm_agent.config import ENCODING, PRODUCT_FEATURE_RX, TOOL_TIMEOUT, settings
from lm_agent.exceptions import LicenseManagerBadServerOutput, LicenseManagerNonSupportedServerTypeError
from lm_agent.logs import logger
from lm_agent.parsing import flexlm, rlm
from lm_agent.workload_managers.slurm.cmd_utils import scontrol_show_lic


class LicenseServerInterface(metaclass=abc.ABCMeta):
    """
    Abstract class for License Server interface.

    The logic for obtaining the data output from the License Server should be encapsulated in
    the get_output_from_server method.

    After obtaining the output, the parsing and manipulation of the data should be implement in
    the get_report_item method.

    It is expected the license information to be parsed into an LicenseReportItem.
    """

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "get_output_from_server")
            and callable(subclass.get_output_from_server)
            and hasattr(subclass, "get_report_item")
            and callable(subclass.get_report_item)
            or NotImplemented
        )

    @abc.abstractclassmethod
    def get_output_from_server(self, product_feature: str):
        """Return output from license server for the indicated features."""

    @abc.abstractclassmethod
    def get_report_item(self, product_feature: str):
        """Parse license server output into a report item for the indicated feature."""


class FlexLMLicenseServer(LicenseServerInterface):
    """Extract license information from FlexLM license server."""

    def __init__(self, license_servers: typing.List[str]):
        self.license_servers = license_servers
        self.parser = flexlm.parse

    def get_commands_list(self):
        """Generate a list of commands with the available license server hosts."""

        host_ports = [(server.split(":")[1:]) for server in self.license_servers]
        commands_to_run = []
        for host, port in host_ports:
            command_line = f"{settings.LMUTIL_PATH} lmstat -c {port}@{host} -f"
            commands_to_run.append(command_line)
        return commands_to_run

    async def get_output_from_server(self, product_feature: str):
        """Override abstract method to get output from FlexLM license server."""

        # get the list of commands for each license server host
        commands_to_run = self.get_commands_list()

        # run each command in the list, one at a time, until one succeds
        for cmd in commands_to_run:
            feature = product_feature.split(".")[1]
            feature_cmd = f"{cmd} {feature}"
            proc = await asyncio.create_subprocess_shell(
                feature_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
            )

            # block until a check at this host:port succeeds or fails
            stdout, _ = await asyncio.wait_for(proc.communicate(), TOOL_TIMEOUT)
            output = str(stdout, encoding=ENCODING)

            if proc.returncode != 0:
                logger.error(f"Error: {output} | Return Code: {proc.returncode}")
                continue
            return output

        raise RuntimeError("None of the checks for FlexLM succeeded!")

    async def get_report_item(self, product_feature: str):
        """Override abstract method to parse FlexLM license server output into License Report Item."""

        server_output = await self.get_output_from_server(product_feature)
        parsed_output = self.parser(server_output)

        # raise exception if parser didn't output license information
        if (
            not parsed_output.get("total")
            or not parsed_output.get("uses")
            or not parsed_output.get("total", None).get("used")
            or not parsed_output.get("total", None).get("total")
        ):
            raise LicenseManagerBadServerOutput()

        report_item = LicenseReportItem(
            product_feature=product_feature,
            used=parsed_output["total"]["used"],
            total=parsed_output["total"]["total"],
            used_licenses=parsed_output["uses"],
        )

        return report_item


class RLMLicenseServer(LicenseServerInterface):
    """Extract license information from RLM license server."""

    def __init__(self, license_servers: typing.List[str]):
        self.license_servers = license_servers
        self.parser = rlm.parse

    def get_commands_list(self):
        """Generate a list of commands with the available license server hosts."""

        host_ports = [(server.split(":")[1:]) for server in self.license_servers]
        commands_to_run = []
        for host, port in host_ports:
            command_line = f"{settings.RLMUTIL_PATH} rlmstat -c {port}@{host} -a -p"
            commands_to_run.append(command_line)
        return commands_to_run

    async def get_output_from_server(self):
        """Override abstract method to get output from RLM license server."""

        # get the list of commands for each license server host
        commands_to_run = self.get_commands_list()

        # run each command in the list, one at a time, until one succeds
        for cmd in commands_to_run:
            proc = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
            )

            # block until a check at this host:port succeeds or fails
            stdout, _ = await asyncio.wait_for(proc.communicate(), TOOL_TIMEOUT)
            output = str(stdout, encoding=ENCODING)

            if proc.returncode != 0:
                logger.error(f"Error: {output} | Return Code: {proc.returncode}")
                continue
            return output

        raise RuntimeError("None of the checks for RLM succeeded!")

    async def get_report_item(self, product_feature: str):
        """Override abstract method to parse RLM license server output into License Report Item."""

        server_output = await self.get_output_from_server()
        parsed_output = self.parser(server_output)

        current_feature_item = self._filter_current_feature(
            parsed_output["total"], product_feature.split(".")[1]
        )
        used_licenses = self._filter_used_features(parsed_output["uses"], product_feature.split(".")[1])

        # raise exception if parser didn't output license information
        if not current_feature_item or used_licenses is None:
            raise LicenseManagerBadServerOutput()

        report_item = LicenseReportItem(
            product_feature=product_feature,
            used=current_feature_item["used"],
            total=current_feature_item["total"],
            used_licenses=used_licenses,
        )

        return report_item

    def _filter_current_feature(self, parsed_list, feature):
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

    def _filter_used_features(self, parsed_list, feature):
        """
        Get the used information for the specified feature.
        """
        used_licenses = []
        for feature_booked in parsed_list:
            if feature_booked["feature"].count("_") == 0:
                if feature_booked["feature"] == feature:
                    used_licenses.append(feature_booked)
            elif "".join(feature_booked["feature"].split("_")[1:]) == feature:
                used_licenses.append(feature_booked)

        for license in used_licenses:
            # remove the feature key, since we already handled it.
            del license["feature"]

        return used_licenses


class LicenseReportItem(BaseModel):
    """
    An item in a LicenseReport, a count of tokens for one product/feature.
    """

    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    used: int
    total: int
    used_licenses: typing.List


def get_all_product_features_from_cluster(show_lic_output: str) -> typing.List[str]:
    """
    Returns a list of all product.feature in the cluster.
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
    Get stat counts using a license stat tool.

    This function iterates over the available license_servers and associated
    features configured via LICENSE_SERVER_FEATURES and generates
    a report by requesting license information from the license_server_type.

    The return from the license server is used to reconcile license-manager's
    view of what features are available with what actually exists in the
    license server database.
    """
    report_items = []

    license_configurations = await get_config_from_backend()
    local_licenses = get_all_product_features_from_cluster(await scontrol_show_lic())
    filtered_entries = get_local_license_configurations(license_configurations, local_licenses)

    license_server_interface: LicenseServerInterface

    server_type_map = dict(
        flexlm=FlexLMLicenseServer,
        rlm=RLMLicenseServer,
    )

    for entry in filtered_entries:
        product_features_to_check = []
        for feature in entry.features.keys():
            product_feature = f"{entry.product}.{feature}"
            product_features_to_check.append(product_feature)

        server_type = server_type_map.get(entry.license_server_type)

        if server_type is None:
            raise LicenseManagerNonSupportedServerTypeError()

        license_server_interface = server_type(entry.license_servers)

        for product_feature in product_features_to_check:
            report_item = await license_server_interface.get_report_item(product_feature)
            report_items.append(report_item)

    reconciliation = [item.dict() for item in report_items]

    return reconciliation
