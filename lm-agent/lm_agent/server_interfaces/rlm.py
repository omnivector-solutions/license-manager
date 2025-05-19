"""RLM license server interface."""
import typing

from lm_agent.models import LicenseServerSchema, LicenseReportItem
from lm_agent.config import settings
from lm_agent.exceptions import CommandFailedToExecute, LicenseManagerBadServerOutput
from lm_agent.logs import logger
from lm_agent.parsing import rlm
from lm_agent.server_interfaces.license_server_interface import LicenseServerInterface
from lm_agent.utils import run_command


class RLMLicenseServer(LicenseServerInterface):
    """Extract license information from RLM license server."""

    def __init__(self, license_servers: typing.List[LicenseServerSchema]):
        self.license_servers = license_servers
        self.parser = rlm.parse

    def get_commands_list(self) -> typing.List[typing.List[str]]:
        """Generate a list of commands with the available license server hosts."""

        commands_to_run = []
        for license_server in self.license_servers:
            command_line = [
                f"{settings.RLMUTIL_PATH}",
                "rlmstat",
                "-c",
                f"{license_server.port}@{license_server.host}",
                "-a",
                "-p",
            ]
            commands_to_run.append(command_line)
        return commands_to_run

    async def get_output_from_server(self):
        """Override abstract method to get output from RLM license server."""

        # get the list of commands for each license server host
        commands_to_run = self.get_commands_list()

        # run each command in the list, one at a time, until one succeds
        for cmd in commands_to_run:
            try:
                output = await run_command(cmd)
            except CommandFailedToExecute as e:
                logger.debug(f"Command {cmd} failed to execute: {e}")
                continue

            # try the next server if the previous didn't return the expected data
            if not output:
                continue
            return output

        raise RuntimeError("None of the checks for RLM succeeded!")

    async def get_report_item(self, feature_id: int, product_feature: str):
        """Override abstract method to parse RLM license server output into License Report Item."""

        server_output = await self.get_output_from_server()
        parsed_output = self.parser(server_output)

        (_, feature) = product_feature.split(".")

        current_feature_item = parsed_output.get(feature)

        # raise exception if parser didn't output license information
        if current_feature_item is None:
            raise LicenseManagerBadServerOutput("Invalid data returned from parser.")

        report_item = LicenseReportItem(
            feature_id=feature_id,
            product_feature=product_feature,
            used=current_feature_item["used"],
            total=current_feature_item["total"],
            uses=current_feature_item["uses"],
        )

        return report_item
