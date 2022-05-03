"""
Invoke license stat tools to build a view of license token counts.
"""
import re
import typing

from lm_agent.backend_utils import BackendConfigurationRow, get_config_from_backend
from lm_agent.exceptions import LicenseManagerBadServerOutput, LicenseManagerNonSupportedServerTypeError
from lm_agent.logs import logger
from lm_agent.server_interfaces.flexlm import FlexLMLicenseServer
from lm_agent.server_interfaces.license_server_interface import LicenseServerInterface
from lm_agent.server_interfaces.lmx import LMXLicenseServer
from lm_agent.server_interfaces.lsdyna import LSDynaLicenseServer
from lm_agent.server_interfaces.rlm import RLMLicenseServer
from lm_agent.workload_managers.slurm.cmd_utils import get_all_product_features_from_cluster


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
                break
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
    local_licenses = await get_all_product_features_from_cluster()
    filtered_entries = get_local_license_configurations(license_configurations, local_licenses)

    logger.debug("#### Getting reconciliation report ####")
    logger.debug("### Licenses in the backend: ")
    logger.debug(license_configurations)
    logger.debug("### Licenses in the cluster: ")
    logger.debug(filtered_entries)

    license_server_interface: LicenseServerInterface

    server_type_map = dict(
        flexlm=FlexLMLicenseServer,
        rlm=RLMLicenseServer,
        lsdyna=LSDynaLicenseServer,
        lmx=LMXLicenseServer,
    )

    for entry in filtered_entries:
        product_features_to_check = []
        for feature in entry.features.keys():
            product_feature = f"{entry.product}.{feature}"
            product_features_to_check.append(product_feature)

        logger.debug("### Features to check: ")
        logger.debug(product_features_to_check)

        server_type = server_type_map.get(entry.license_server_type)

        if server_type is None:
            raise LicenseManagerNonSupportedServerTypeError()

        license_server_interface = server_type(entry.license_servers)

        for product_feature in product_features_to_check:
            try:
                report_item = await license_server_interface.get_report_item(product_feature)
                report_items.append(report_item)
            except LicenseManagerBadServerOutput:
                logger.error(f"#### Report for feature {product_feature} failed! ####")
                continue

    reconciliation = [item.dict() for item in report_items]
    logger.debug("#### Reconciliation items:")
    logger.debug(reconciliation)

    return reconciliation
