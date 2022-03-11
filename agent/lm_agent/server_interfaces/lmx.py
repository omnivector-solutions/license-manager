"""LM-X license server interface."""
import typing

from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBadServerOutput
from lm_agent.parsing import lmx
from lm_agent.server_interfaces.license_server_interface import LicenseReportItem, LicenseServerInterface
from lm_agent.server_interfaces.utils import run_command


class LMXLicenseServer(LicenseServerInterface):
    """Extract license information from LM-X license server."""

    def __init__(self, license_servers: typing.List[str]):
        """Initialize the license server instance with the license server host and parser."""
        self.license_servers = license_servers
        self.parser = lmx.parse

    def get_commands_list(self):
        """Generate a list of commands with the available license server hosts."""

        host_ports = [(server.split(":")[1:]) for server in self.license_servers]
        commands_to_run = []
        for host, port in host_ports:
            command_line = f"{settings.LMXENDUTIL_PATH} -licstat -host {host} -port {port}"
            commands_to_run.append(command_line)
        return commands_to_run

    async def get_output_from_server(self):
        """Override abstract method to get output from LM-X license server."""

        # get the list of commands for each license server host
        commands_to_run = self.get_commands_list()

        # run each command in the list, one at a time, until one succeds
        for cmd in commands_to_run:
            output = await run_command(cmd)

            # try the next server if the previous didn't return the expected data
            if output is None:
                continue
            return output

        raise RuntimeError("None of the checks for LM-X succeeded!")

    async def get_report_item(self, product_feature: str):
        """Override abstract method to parse LM-X license server output into License Report Item."""

        server_output = await self.get_output_from_server()
        parsed_output = self.parser(server_output)

        (_, feature) = product_feature.split(".")

        current_feature_item = parsed_output.get(feature)

        # raise exception if parser didn't output license information
        if current_feature_item is None:
            raise LicenseManagerBadServerOutput("Invalid data returned from parser.")

        report_item = LicenseReportItem(
            product_feature=product_feature,
            used=current_feature_item["used"],
            total=current_feature_item["total"],
            used_licenses=current_feature_item["uses"],
        )

        return report_item
