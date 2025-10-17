from unittest import mock

from httpx import Response
from pytest import mark, raises

from lm_agent.exceptions import LicenseManagerBackendConnectionError, LicenseManagerEmptyReportError
from lm_agent.models import (
    ConfigurationSchema,
    FeatureSchema,
    LicenseReportItem,
    LicenseServerSchema,
    LicenseServerType,
    ProductSchema,
)
from lm_agent.services import license_report


@mark.asyncio
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "flexlm_output",
            [
                {
                    "feature_id": 1,
                    "product_feature": "testproduct.testfeature",
                    "used": 93,
                    "total": 1000,
                    "uses": [
                        {"booked": 29, "username": "sdmfva", "lead_host": "myserver.example.com"},
                        {"booked": 27, "username": "adfdna", "lead_host": "myserver.example.com"},
                        {"booked": 37, "username": "sdmfva", "lead_host": "myserver.example.com"},
                    ],
                },
            ],
        ),
    ],
)
@mock.patch("lm_agent.server_interfaces.flexlm.FlexLMLicenseServer.get_output_from_server")
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
async def test_flexlm_get_report(
    get_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    get_output_from_server_mock: mock.MagicMock,
    output,
    reconciliation,
    one_configuration_row_flexlm,
    scontrol_show_lic_output_flexlm,
    request,
):
    """
    Do I get a report for the FlexLM licenses in the cluster?
    """
    get_configs_from_backend_mock.return_value = [one_configuration_row_flexlm]
    show_lic_mock.return_value = scontrol_show_lic_output_flexlm

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output

    reconcile_list = await license_report.report()
    assert reconcile_list == [LicenseReportItem(**item) for item in reconciliation]


@mark.asyncio
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "rlm_output",
            [
                {
                    "feature_id": 1,
                    "product_feature": "converge.converge_super",
                    "used": 93,
                    "total": 1000,
                    "uses": [
                        {"booked": 29, "username": "asdj13", "lead_host": "myserver.example.com"},
                        {"booked": 27, "username": "cddcp2", "lead_host": "myserver.example.com"},
                        {"booked": 37, "username": "asdj13", "lead_host": "myserver.example.com"},
                    ],
                },
            ],
        ),
        (
            "rlm_output_no_licenses",
            [
                {
                    "feature_id": 1,
                    "product_feature": "converge.converge_super",
                    "used": 0,
                    "total": 1000,
                    "uses": [],
                },
            ],
        ),
    ],
)
@mock.patch("lm_agent.server_interfaces.rlm.RLMLicenseServer.get_output_from_server")
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
async def test_rlm_get_report(
    get_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    get_output_from_server_mock: mock.MagicMock,
    output,
    reconciliation,
    one_configuration_row_rlm,
    scontrol_show_lic_output_rlm,
    request,
):
    """
    Do I get a report for the RLM licenses in the cluster?
    """
    get_configs_from_backend_mock.return_value = [one_configuration_row_rlm]
    show_lic_mock.return_value = scontrol_show_lic_output_rlm

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output

    reconcile_list = await license_report.report()
    assert reconcile_list == [LicenseReportItem(**item) for item in reconciliation]


@mark.asyncio
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "lsdyna_output",
            [
                {
                    "feature_id": 1,
                    "product_feature": "mppdyna.mppdyna",
                    "used": 440,
                    "total": 500,
                    "uses": [
                        {"booked": 80, "username": "dvds3g", "lead_host": "n-c13.com"},
                        {"booked": 80, "username": "ssss1d", "lead_host": "n-c52.com"},
                        {"booked": 80, "username": "ssss1d", "lead_host": "n-c15.com"},
                        {"booked": 80, "username": "ywap0o", "lead_host": "n-c53.com"},
                        {"booked": 80, "username": "ywap0o", "lead_host": "n-c51.com"},
                        {"booked": 40, "username": "ndha1a", "lead_host": "n-c55.com"},
                    ],
                },
            ],
        ),
        (
            "lsdyna_output_no_licenses",
            [
                {
                    "feature_id": 1,
                    "product_feature": "mppdyna.mppdyna",
                    "used": 0,
                    "total": 500,
                    "uses": [],
                },
            ],
        ),
    ],
)
@mock.patch("lm_agent.server_interfaces.lsdyna.LSDynaLicenseServer.get_output_from_server")
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
async def test_lsdyna_get_report(
    get_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    get_output_from_server_mock: mock.MagicMock,
    output,
    reconciliation,
    one_configuration_row_lsdyna,
    scontrol_show_lic_output_lsdyna,
    request,
):
    """
    Do I get a report for the LS-Dyna licenses in the cluster?
    """
    get_configs_from_backend_mock.return_value = [one_configuration_row_lsdyna]
    show_lic_mock.return_value = scontrol_show_lic_output_lsdyna

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output

    reconcile_list = await license_report.report()
    assert reconcile_list == [LicenseReportItem(**item) for item in reconciliation]


@mark.asyncio
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "lmx_output",
            [
                LicenseReportItem(
                    feature_id=1,
                    product_feature="hyperworks.hyperworks",
                    used=25000,
                    total=1000000,
                    uses=[
                        {
                            "booked": 25000,
                            "username": "sssaah",
                            "lead_host": "RD0082406",
                        }
                    ],
                ),
            ],
        ),
        (
            "lmx_output_no_licenses",
            [
                LicenseReportItem(
                    feature_id=1,
                    product_feature="hyperworks.hyperworks",
                    used=0,
                    total=1000000,
                    uses=[],
                ),
            ],
        ),
    ],
)
@mock.patch("lm_agent.server_interfaces.lmx.LMXLicenseServer.get_output_from_server")
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
async def test_lmx_get_report(
    get_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    get_output_from_server_mock: mock.MagicMock,
    output,
    reconciliation,
    one_configuration_row_lmx,
    scontrol_show_lic_output_lmx: str,
    request,
):
    """
    Do I get a report for the LM-X licenses in the cluster?
    """
    get_configs_from_backend_mock.return_value = [one_configuration_row_lmx]
    show_lic_mock.return_value = scontrol_show_lic_output_lmx

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output

    reconcile_list = await license_report.report()
    assert reconcile_list == reconciliation


@mark.asyncio
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "olicense_output",
            [
                LicenseReportItem(
                    feature_id=1,
                    product_feature="cosin.ftire_adams",
                    used=3,
                    total=4,
                    uses=[
                        {"username": "sbhyma", "lead_host": "RD0087712", "booked": 1},
                        {"username": "sbhyma", "lead_host": "RD0087713", "booked": 1},
                        {"username": "user22", "lead_host": "RD0087713", "booked": 1},
                    ],
                ),
            ],
        ),
        (
            "olicense_output_no_licenses",
            [
                LicenseReportItem(
                    feature_id=1,
                    product_feature="cosin.ftire_adams",
                    used=0,
                    total=4,
                    uses=[],
                ),
            ],
        ),
    ],
)
@mock.patch("lm_agent.server_interfaces.olicense.OLicenseLicenseServer.get_output_from_server")
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
async def test_olicense_get_report(
    get_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    get_output_from_server_mock: mock.MagicMock,
    output,
    reconciliation,
    one_configuration_row_olicense,
    scontrol_show_lic_output_olicense: str,
    request,
):
    """
    Do I get a report for the OLicense licenses in the cluster?
    """
    get_configs_from_backend_mock.return_value = [one_configuration_row_olicense]
    show_lic_mock.return_value = scontrol_show_lic_output_olicense

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output
    reconcile_list = await license_report.report()
    assert reconcile_list == reconciliation


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
async def test_flexlm_report_with_empty_backend(
    get_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_flexlm,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_configs_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_flexlm

    reconcile_list = await license_report.report()
    assert reconcile_list == []


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
async def test_rlm_report_with_empty_backend(
    get_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_rlm,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_configs_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_rlm

    reconcile_list = await license_report.report()
    assert reconcile_list == []


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
async def test_lsdyna_report_with_empty_backend(
    get_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_lsdyna,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_configs_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_lsdyna

    reconcile_list = await license_report.report()
    assert reconcile_list == []


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
async def test_lmx_report_with_empty_backend(
    get_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_lmx: str,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_configs_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_lmx

    reconcile_list = await license_report.report()
    assert reconcile_list == []


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
async def test_olicense_report_with_empty_backend(
    get_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_olicense: str,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_configs_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_olicense

    reconcile_list = await license_report.report()
    assert reconcile_list == []


def test_get_local_license_configurations():
    configuration_super = ConfigurationSchema(
        id=1,
        name="Converge",
        cluster_client_id="dummy",
        features=[
            FeatureSchema(
                id=1,
                name="converge_super",
                product=ProductSchema(id=1, name="converge"),
                config_id=1,
                reserved=100,
                total=1000,
                used=93,
                booked_total=0,
            )
        ],
        license_servers=[
            LicenseServerSchema(id=1, config_id=1, host="licserv0001", port=1234),
            LicenseServerSchema(id=3, config_id=1, host="licserv0003", port=8760),
        ],
        grace_time=60,
        type=LicenseServerType.RLM,
    )

    configuration_polygonica = ConfigurationSchema(
        id=2,
        name="Converge GUI Polygonica",
        cluster_client_id="dummy",
        features=[
            FeatureSchema(
                id=2,
                name="converge_gui_polygonica",
                product=ProductSchema(id=1, name="converge"),
                config_id=2,
                reserved=100,
                total=1000,
                used=93,
                booked_total=0,
            )
        ],
        license_servers=[
            LicenseServerSchema(id=1, config_id=2, host="licserv0001", port=1234),
            LicenseServerSchema(id=3, config_id=2, host="licserv0003", port=8760),
        ],
        grace_time=60,
        type=LicenseServerType.RLM,
    )

    license_configurations = [configuration_super, configuration_polygonica]
    local_licenses = ["converge.converge_super"]

    assert license_report.get_local_license_configurations(license_configurations, local_licenses) == [
        configuration_super
    ]


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
@mock.patch("lm_agent.services.license_report.get_local_license_configurations")
@mock.patch("lm_agent.services.license_report.RLMLicenseServer.get_report_item")
async def test_license_report_empty_on_exception_raised(
    get_report_item_mock: mock.MagicMock,
    get_local_license_configurations_mock: mock.MagicMock,
    get_cluster_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
):
    """
    Do I get an empty report when an exception is raised?
    """
    get_cluster_configs_from_backend_mock.return_value = []
    show_lic_mock.return_value = ""
    get_local_license_configurations_mock.return_value = [
        ConfigurationSchema(
            id=1,
            name="Converge",
            cluster_client_id="dummy",
            features=[
                FeatureSchema(
                    id=1,
                    name="converge_super",
                    product=ProductSchema(id=1, name="converge"),
                    config_id=1,
                    reserved=100,
                    total=1000,
                    used=93,
                    booked_total=0,
                )
            ],
            license_servers=[
                LicenseServerSchema(id=1, config_id=1, host="licserv0001", port=1234),
                LicenseServerSchema(id=3, config_id=1, host="licserv0003", port=8760),
            ],
            grace_time=60,
            type=LicenseServerType.RLM,
        )
    ]
    get_report_item_mock.side_effect = Exception("Something is wrong with the license server!")

    assert await license_report.report() == [
        LicenseReportItem(
            feature_id=1,
            product_feature="converge.converge_super",
            used=0,
            total=0,
            uses=[],
        )
    ]


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.services.license_report.get_cluster_configs_from_backend")
@mock.patch("lm_agent.services.license_report.get_local_license_configurations")
@mock.patch("lm_agent.services.license_report.RLMLicenseServer.get_report_item")
async def test_license_report_empty_on_exception_raised_with_multiple_features(
    get_report_item_mock: mock.MagicMock,
    get_local_license_configurations_mock: mock.MagicMock,
    get_cluster_configs_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
):
    """
    Do I get an empty report when an exception is raised?
    """
    get_cluster_configs_from_backend_mock.return_value = []
    show_lic_mock.return_value = ""
    get_local_license_configurations_mock.return_value = [
        ConfigurationSchema(
            id=1,
            name="Converge",
            cluster_client_id="dummy",
            features=[
                FeatureSchema(
                    id=1,
                    name="converge_super",
                    product=ProductSchema(id=1, name="converge"),
                    config_id=1,
                    reserved=100,
                    total=1000,
                    used=93,
                    booked_total=0,
                )
            ],
            license_servers=[
                LicenseServerSchema(id=1, config_id=1, host="licserv0001", port=1234),
                LicenseServerSchema(id=3, config_id=1, host="licserv0003", port=8760),
            ],
            grace_time=60,
            type=LicenseServerType.RLM,
        ),
        ConfigurationSchema(
            id=2,
            name="Converge GUI Polygonica",
            cluster_client_id="dummy",
            features=[
                FeatureSchema(
                    id=2,
                    name="converge_gui_polygonica",
                    product=ProductSchema(id=1, name="converge"),
                    config_id=2,
                    reserved=100,
                    total=1000,
                    used=93,
                    booked_total=0,
                )
            ],
            license_servers=[
                LicenseServerSchema(id=1, config_id=2, host="licserv0001", port=1234),
                LicenseServerSchema(id=3, config_id=2, host="licserv0003", port=8760),
            ],
            grace_time=60,
            type=LicenseServerType.RLM,
        ),
    ]
    get_report_item_mock.side_effect = Exception("Something is wrong with the license server!")

    assert await license_report.report() == [
        LicenseReportItem(
            feature_id=1,
            product_feature="converge.converge_super",
            used=0,
            total=0,
            uses=[],
        ),
        LicenseReportItem(
            feature_id=2,
            product_feature="converge.converge_gui_polygonica",
            used=0,
            total=0,
            uses=[],
        ),
    ]


@mark.asyncio
@mock.patch("lm_agent.services.license_report.report")
async def test__update_features__report_empty(report_mock):
    """
    Check the correct behavior when the report is empty in reconcile.
    """
    report_mock.return_value = []
    with raises(LicenseManagerEmptyReportError):
        await license_report.update_features()


@mark.asyncio
@mark.respx(base_url="http://backend")
@mock.patch("lm_agent.services.license_report.report")
async def test__update_features__put_failed(
    report_mock,
    respx_mock,
):
    """
    Check that when put /features/bulk status_code is not 200, should raise exception.
    """
    report_mock.return_value = [
        LicenseReportItem(
            feature_id=1,
            product_feature="abaqus.abaqus",
            total=1000,
            used=200,
            uses=[],
        )
    ]

    respx_mock.put("/lm/features/bulk").mock(return_value=Response(status_code=400))

    with raises(LicenseManagerBackendConnectionError):
        await license_report.update_features()
