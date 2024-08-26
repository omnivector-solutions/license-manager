from unittest import mock

from pytest import mark
from lm_agent.models import LicenseReportItem
from lm_agent.services.reconciliation import reconcile


@mark.asyncio
@mock.patch("lm_agent.services.reconciliation.return_formatted_squeue_out")
@mock.patch("lm_agent.services.reconciliation.create_or_update_reservation")
@mock.patch("lm_agent.services.reconciliation.get_all_features_cluster_values")
@mock.patch("lm_agent.services.reconciliation.get_cluster_configs_from_backend")
@mock.patch("lm_agent.services.reconciliation.get_all_features_bookings_sum")
@mock.patch("lm_agent.services.reconciliation.get_cluster_jobs_from_backend")
@mock.patch("lm_agent.services.reconciliation.update_features")
async def test__reconcile__success(
    update_features_mock,
    get_jobs_from_backend_mock,
    get_bookings_sum_mock,
    get_configs_from_backend_mock,
    get_all_cluster_values_mock,
    create_or_update_reservation_mock,
    return_formatted_squeue_out_mock,
    parsed_configurations,
):
    """
    Check if reconcile updates the reservation with the correct value.
    The reservation should block all licenses that are in use.

    License: abaqus.abaqus@flexlm
    Total: 1000

    Cluster: cluster1
    Used in cluster: 23

    Overview of the license:
    _________________________________________________________________
    |    200   |    15     |     17    |    71    |       697       |
    |   used   |   booked  |   booked  |  booked  |      free       |
    | Lic serv | cluster 1 | cluster 2 | cluster3 |     to use      |
    -----------------------------------------------------------------

    Since we have 303 licenses in use (booked or license server), the
    amount of licenses available is 697.

    This way, we need to block the 303 licenses that are in use.
    But considering that Slurm is already "blocking" 23 licenses
    that are in use in the cluster, the reservation should block 280 licenses.

    Formula to calculate the reservation:
    reservation = lic serv used - slurm used + booked sum
    reservation = 200 - 23 + 103 = 280

    """
    update_features_mock.return_value = [
        LicenseReportItem(
            feature_id=1,
            product_feature="abaqus.abaqus",
            total=1000,
            used=200,
            uses=[],
        )
    ]
    get_configs_from_backend_mock.return_value = parsed_configurations
    get_jobs_from_backend_mock.return_value = []
    get_bookings_sum_mock.return_value = {"abaqus.abaqus": 103}
    get_all_cluster_values_mock.return_value = {"abaqus.abaqus": {"total": 1000, "used": 23}}
    return_formatted_squeue_out_mock.return_value = ""

    await reconcile()
    create_or_update_reservation_mock.assert_called_with("abaqus.abaqus@flexlm:280")
