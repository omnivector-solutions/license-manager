from textwrap import dedent
from unittest import mock

from pytest import fixture, mark

from lm_agent import tokenstat
from lm_agent.backend_utils import BackendConfigurationRow


@mark.asyncio
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "lmstat_output",
            [
                {
                    "product_feature": "testproduct.testfeature",
                    "used": 93,
                    "total": 1000,
                    "used_licenses": [
                        {
                            "user_name": "jbemfv",
                            "lead_host": "myserver.example.com",
                            "booked": 29,
                        },
                        {
                            "user_name": "cdxfdn",
                            "lead_host": "myserver.example.com",
                            "booked": 27,
                        },
                        {
                            "user_name": "jbemfv",
                            "lead_host": "myserver.example.com",
                            "booked": 37,
                        },
                    ],
                },
            ],
        ),
    ],
)
@mock.patch("lm_agent.server_interfaces.flexlm.FlexLMLicenseServer.get_output_from_server")
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_flexlm_get_report(
    get_config_from_backend_mock: mock.MagicMock,
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
    get_config_from_backend_mock.return_value = [one_configuration_row_flexlm]
    show_lic_mock.return_value = scontrol_show_lic_output_flexlm

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output

    reconcile_list = await tokenstat.report()
    assert reconcile_list == reconciliation


@mark.asyncio
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "rlm_output",
            [
                {
                    "product_feature": "converge.converge_super",
                    "used": 93,
                    "total": 1000,
                    "used_licenses": [
                        {
                            "user_name": "jbemfv",
                            "lead_host": "myserver.example.com",
                            "booked": 29,
                        },
                        {
                            "user_name": "cdxfdn",
                            "lead_host": "myserver.example.com",
                            "booked": 27,
                        },
                        {
                            "user_name": "jbemfv",
                            "lead_host": "myserver.example.com",
                            "booked": 37,
                        },
                    ],
                },
            ],
        ),
        (
            "rlm_output_no_licenses",
            [
                {
                    "product_feature": "converge.converge_super",
                    "used": 0,
                    "total": 1000,
                    "used_licenses": [],
                },
            ],
        ),
    ],
)
@mock.patch("lm_agent.server_interfaces.rlm.RLMLicenseServer.get_output_from_server")
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_rlm_get_report(
    get_config_from_backend_mock: mock.MagicMock,
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
    get_config_from_backend_mock.return_value = [one_configuration_row_rlm]
    show_lic_mock.return_value = scontrol_show_lic_output_rlm

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output

    reconcile_list = await tokenstat.report()
    assert reconcile_list == reconciliation


@mark.asyncio
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "lsdyna_output",
            [
                {
                    "product_feature": "mppdyna.mppdyna",
                    "used": 440,
                    "total": 500,
                    "used_licenses": [
                        {"user_name": "fane8y", "lead_host": "n-c13.maas.rnd.com", "booked": 80},
                        {"user_name": "ssskmj", "lead_host": "n-c52.maas.rnd.com", "booked": 80},
                        {"user_name": "ssskmj", "lead_host": "n-c15.maas.rnd.com", "booked": 80},
                        {"user_name": "ywazrn", "lead_host": "n-c53.maas.rnd.com", "booked": 80},
                        {"user_name": "ywazrn", "lead_host": "n-c51.maas.rnd.com", "booked": 80},
                        {"user_name": "ndhtw9", "lead_host": "n-c55.maas.rnd.com", "booked": 40},
                    ],
                },
            ],
        ),
        (
            "lsdyna_output_no_licenses",
            [
                {
                    "product_feature": "mppdyna.mppdyna",
                    "used": 0,
                    "total": 500,
                    "used_licenses": [],
                },
            ],
        ),
    ],
)
@mock.patch("lm_agent.server_interfaces.lsdyna.LSDynaLicenseServer.get_output_from_server")
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_lsdyna_get_report(
    get_config_from_backend_mock: mock.MagicMock,
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
    get_config_from_backend_mock.return_value = [one_configuration_row_lsdyna]
    show_lic_mock.return_value = scontrol_show_lic_output_lsdyna

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output

    reconcile_list = await tokenstat.report()
    assert reconcile_list == reconciliation


@mark.asyncio
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "lmx_output",
            [
                {
                    "product_feature": "hyperworks.hyperworks",
                    "used": 25000,
                    "total": 1000000,
                    "used_licenses": [
                        {"user_name": "sssaah", "lead_host": "RD0082406", "booked": 25000},
                    ],
                }
            ],
        ),
        (
            "lmx_output_no_licenses",
            [
                {
                    "product_feature": "hyperworks.hyperworks",
                    "used": 0,
                    "total": 1000000,
                    "used_licenses": [],
                },
            ],
        ),
    ],
)
@mock.patch("lm_agent.server_interfaces.lmx.LMXLicenseServer.get_output_from_server")
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_lmx_get_report(
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    get_output_from_server_mock: mock.MagicMock,
    output: str,
    reconciliation: dict,
    one_configuration_row_lmx: BackendConfigurationRow,
    scontrol_show_lic_output_lmx: str,
    request,
):
    """
    Do I get a report for the LM-X licenses in the cluster?
    """
    get_config_from_backend_mock.return_value = [one_configuration_row_lmx]
    show_lic_mock.return_value = scontrol_show_lic_output_lmx

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output

    reconcile_list = await tokenstat.report()
    assert reconcile_list == reconciliation


@mark.asyncio
@mark.parametrize(
    "output,reconciliation",
    [
        (
            "olicense_output",
            [
                {
                    "product_feature": "cosin.ftire_adams",
                    "used": 3,
                    "total": 4,
                    "used_licenses": [
                        {"user_name": "sbhyma", "lead_host": "RD0087712", "booked": 1},
                        {"user_name": "sbhyma", "lead_host": "RD0087713", "booked": 1},
                        {"user_name": "user22", "lead_host": "RD0087713", "booked": 1},
                    ],
                },
            ],
        ),
        (
            "olicense_output_no_licenses",
            [
                {
                    "product_feature": "cosin.ftire_adams",
                    "used": 0,
                    "total": 4,
                    "used_licenses": [],
                },
            ],
        ),
    ],
)
@mock.patch("lm_agent.server_interfaces.olicense.OLicenseLicenseServer.get_output_from_server")
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_olicense_get_report(
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    get_output_from_server_mock: mock.MagicMock,
    output: str,
    reconciliation: dict,
    one_configuration_row_olicense: BackendConfigurationRow,
    scontrol_show_lic_output_olicense: str,
    request,
):
    """
    Do I get a report for the OLicense licenses in the cluster?
    """
    get_config_from_backend_mock.return_value = [one_configuration_row_olicense]
    show_lic_mock.return_value = scontrol_show_lic_output_olicense

    output = request.getfixturevalue(output)
    get_output_from_server_mock.return_value = output

    reconcile_list = await tokenstat.report()
    assert reconcile_list == reconciliation


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_flexlm_report_with_empty_backend(
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_flexlm,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_config_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_flexlm

    reconcile_list = await tokenstat.report()
    assert reconcile_list == []


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_rlm_report_with_empty_backend(
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_rlm,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_config_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_rlm

    reconcile_list = await tokenstat.report()
    assert reconcile_list == []


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_lsdyna_report_with_empty_backend(
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_lsdyna,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_config_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_lsdyna

    reconcile_list = await tokenstat.report()
    assert reconcile_list == []


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_lmx_report_with_empty_backend(
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_lmx: str,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_config_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_lmx

    reconcile_list = await tokenstat.report()
    assert reconcile_list == []


@mark.asyncio
@mock.patch("lm_agent.workload_managers.slurm.cmd_utils.scontrol_show_lic")
@mock.patch("lm_agent.tokenstat.get_config_from_backend")
async def test_olicense_report_with_empty_backend(
    get_config_from_backend_mock: mock.MagicMock,
    show_lic_mock: mock.MagicMock,
    scontrol_show_lic_output_olicense: str,
):
    """
    Do I collect the requested structured data when the backend is empty?
    """
    get_config_from_backend_mock.return_value = []
    show_lic_mock.return_value = scontrol_show_lic_output_olicense

    reconcile_list = await tokenstat.report()
    assert reconcile_list == []


def test_get_local_license_configurations():
    configuration_super = BackendConfigurationRow(
        product="converge",
        features={"converge_super": 10},
        license_servers=["rlm:127.0.0.1:2345"],
        license_server_type="rlm",
        grace_time=10000,
        client_id="cluster-staging",
    )

    configuration_polygonica = BackendConfigurationRow(
        product="converge",
        features={"converge_gui_polygonica": 10},
        license_servers=["rlm:127.0.0.1:2345"],
        license_server_type="rlm",
        grace_time=10000,
        client_id="cluster-staging",
    )

    license_configurations = [configuration_super, configuration_polygonica]
    local_licenses = ["converge.converge_super"]

    assert tokenstat.get_local_license_configurations(license_configurations, local_licenses) == [
        configuration_super
    ]
