import typing

from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBadServerOutput
from lm_agent.parsing import rlm
from lm_agent.server_interfaces.license_server_interface import LicenseReportItem, LicenseServerInterface
from lm_agent.server_interfaces.utils import run_command


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
            output = await run_command(cmd)

            # try the next server if the previous didn't return the expected data
            if output is None:
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
        if current_feature_item is None or used_licenses is None:
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