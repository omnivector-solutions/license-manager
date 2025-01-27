"""
Invoke license stat tools to build a view of license token counts.
"""
import asyncio
import typing

from lm_agent.models import ConfigurationSchema, LicenseReportItem
from lm_agent.backend_utils.utils import get_cluster_configs_from_backend, make_feature_update
from lm_agent.exceptions import LicenseManagerNonSupportedServerTypeError, LicenseManagerEmptyReportError
from lm_agent.logs import logger
from lm_agent.server_interfaces.flexlm import FlexLMLicenseServer
from lm_agent.server_interfaces.lmx import LMXLicenseServer
from lm_agent.server_interfaces.lsdyna import LSDynaLicenseServer
from lm_agent.server_interfaces.olicense import OLicenseLicenseServer
from lm_agent.server_interfaces.rlm import RLMLicenseServer
from lm_agent.server_interfaces.dsls import DSLSLicenseServer
from lm_agent.workload_managers.slurm.cmd_utils import get_all_product_features_from_cluster


def get_local_license_configurations(
    license_configurations: typing.List[ConfigurationSchema], local_licenses: typing.List[str]
) -> typing.List[ConfigurationSchema]:
    """
    Return the license configurations from the backend that are configured on the cluster.
    """
    filtered_entries = []

    for entry in license_configurations:
        for feature in entry.features:
            feature_name = feature.name
            product_name = feature.product.name
            if f"{product_name}.{feature_name}" in local_licenses:
                filtered_entries.append(entry)
                break
    return filtered_entries


async def report() -> typing.List[LicenseReportItem]:
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
    get_report_awaitables = []
    product_features_awaited = []

    # Get cluster configuration
    license_configurations = await get_cluster_configs_from_backend()

    local_licenses = await get_all_product_features_from_cluster()
    filtered_entries = get_local_license_configurations(license_configurations, local_licenses)

    logger.debug("#### Getting reconciliation report ####")
    logger.debug("### Licenses in the backend: ")
    logger.debug(license_configurations)
    logger.debug("### Licenses in the cluster: ")
    logger.debug(filtered_entries)

    server_type_map = dict(
        flexlm=FlexLMLicenseServer,
        rlm=RLMLicenseServer,
        lsdyna=LSDynaLicenseServer,
        lmx=LMXLicenseServer,
        olicense=OLicenseLicenseServer,
        dsls=DSLSLicenseServer,
    )

    for entry in filtered_entries:
        product_features_to_check = []
        for feature in entry.features:
            feature_info = (feature.id, f"{feature.product.name}.{feature.name}")
            product_features_to_check.append(feature_info)

        logger.debug("### Features to check: ")
        logger.debug(product_features_to_check)

        server_type = server_type_map.get(entry.type)

        if server_type is None:
            raise LicenseManagerNonSupportedServerTypeError("License server type not supported.")

        license_server_interface = server_type(entry.license_servers)

        for feature_info_to_check in product_features_to_check:
            feature_id, product_feature = feature_info_to_check

            get_report_awaitables.append(
                license_server_interface.get_report_item(feature_id, product_feature)
            )
            product_features_awaited.append(feature_info_to_check)

    results: list[BaseException | LicenseReportItem] = await asyncio.gather(
        *get_report_awaitables, return_exceptions=True
    )

    for result, feature_info in zip(results, product_features_awaited):
        feature_id, product_feature = feature_info

        if isinstance(result, Exception):
            # If the report for a feature failed, the total will set to 0, preventing jobs from running
            logger.error(f"#### Report for feature {product_feature} failed with: {str(result)} ####")

            failed_report_item = LicenseReportItem(
                feature_id=feature_id,
                product_feature=product_feature,
                used=0,
                total=0,
                uses=[],
            )
            report_items.append(failed_report_item)
            continue
        assert isinstance(result, LicenseReportItem)
        report_items.append(result)

    logger.debug("#### Reconciliation items:")
    logger.debug(report_items)

    return report_items


async def update_features() -> typing.List[LicenseReportItem]:
    """Send the license data collected from the cluster to the backend."""
    license_report = await report()

    if not license_report:
        logger.critical(
            "No license data could be collected, check that tools are installed "
            "correctly and the right hosts/ports are configured in settings"
        )
        raise LicenseManagerEmptyReportError("Got an empty response from the license server")

    features_to_update = []

    for license in license_report:
        product, feature = license.product_feature.split(".")

        feature_data = {
            "product_name": product,
            "feature_name": feature,
            "total": license.total,
            "used": license.used,
        }

        features_to_update.append(feature_data)

    await make_feature_update(features_to_update)

    return license_report
