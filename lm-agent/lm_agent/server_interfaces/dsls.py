"""DSLS license server interface."""
import typing

from lm_agent.models import LicenseServerSchema, LicenseReportItem
from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBadServerOutput
from lm_agent.server_interfaces.license_server_interface import LicenseServerInterface
from lm_agent.parsing import dsls
from lm_agent.utils import run_command


class DSLSLicenseServer(LicenseServerInterface):
    """Extract license information from DSLS license server."""

    def __init__(self, license_servers: typing.List[LicenseServerSchema]):
        """Initialize the license server instance with the license server host and parser."""
        self.license_servers = license_servers
        self.parser = dsls.parse

    def get_commands_list(self) -> typing.List[typing.Dict]:
        """Generate a list of commands with the available license server hosts."""

        commands_to_run = []
        for license_server in self.license_servers:
            command_input = f"connect {license_server.host} {license_server.port}\ngetLicenseUsage -csv"
            command_line = [f"{settings.DSLICSRV_PATH}", "-admin"]

            commands_to_run.append({"input": command_input, "command": command_line})
        return commands_to_run

    async def get_output_from_server(self):
        """Override abstract method to get output from DSLS license server."""

        # get the list of commands for each license server host
        commands_to_run = self.get_commands_list()

        # run each command in the list, one at a time, until one succeds
        for cmd in commands_to_run:
            output = await run_command(command_line_parts=cmd["command"], stdin_str=cmd["input"])

            # try the next server if the previous didn't return the expected data
            if not output:
                continue
            return output

        raise RuntimeError("None of the checks for DSLS succeeded!")

    async def get_report_item(self, feature_id: int, product_feature: str):
        """Override abstract method to parse DSLS license server output into License Report Item."""

        server_output = await self.get_output_from_server()
        parsed_output = self.parser(server_output)

        (_, feature) = product_feature.split(".")

        current_feature_item = LicenseManagerBadServerOutput.enforce_defined(
            parsed_output.get(feature),
            "Invalid data returned from parser.",
        )

        report_item = LicenseReportItem(
            feature_id=feature_id,
            product_feature=product_feature,
            used=current_feature_item.used,
            total=current_feature_item.total,
            uses=current_feature_item.uses,
        )

        return report_item
