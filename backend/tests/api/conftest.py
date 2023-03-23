from pytest import fixture

from lm_backend.api_schemas import BookingRow, ConfigurationRow
from lm_backend.api_schemas import LicenseUseReconcile as LUR
from lm_backend.constants import LicenseServerType


@fixture
def some_config_rows():
    """
    Sample config_table row.
    """
    return [
        ConfigurationRow(
            id=1,
            name="HelloDolly",
            product="hello",
            features='{"world": {"total": 100, "limit": 100}, "dolly": {"total": 80, "limit": 80}}',
            license_servers=["bla"],
            license_server_type=LicenseServerType.FLEXLM,
            grace_time=10,
            client_id="cluster-staging",
        ),
        ConfigurationRow(
            id=2,
            name="CoolBeans",
            product="cool",
            features='{"beans": {"total": 11, "limit": 11}}',
            license_servers=["bla"],
            license_server_type=LicenseServerType.FLEXLM,
            grace_time=10,
            client_id="cluster-staging",
        ),
        ConfigurationRow(
            id=3,
            name="LimitedLicense",
            product="limited",
            features='{"license": {"total": 50, "limit": 40}}',
            license_servers=["bla"],
            license_server_type=LicenseServerType.FLEXLM,
            grace_time=10,
            client_id="cluster-staging",
        ),
    ]


@fixture
def some_booking_rows():
    """
    Some BookingRows.
    """
    return [
        BookingRow(
            id=1,
            job_id="helloworld",
            product_feature="hello.world",
            booked=19,
            config_id=1,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        BookingRow(
            id=2,
            job_id="hellodolly",
            product_feature="hello.dolly",
            booked=11,
            config_id=1,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        BookingRow(
            id=3,
            job_id="coolbeans",
            product_feature="cool.beans",
            booked=11,
            config_id=2,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        BookingRow(
            id=4,
            job_id="limitedlicense",
            product_feature="limited.license",
            booked=40,
            config_id=3,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
    ]


@fixture
def some_licenses():
    """
    Some LicenseUse bookings
    """
    inserts = [
        LUR(
            product_feature="hello.world",
            total=100,
            used=19,
            used_licenses=[{"booked": 19, "lead_host": "host1", "user_name": "user1"}],
        ),
        LUR(
            product_feature="hello.dolly",
            total=80,
            used=11,
            used_licenses=[{"booked": 11, "lead_host": "host1", "user_name": "user1"}],
        ),
        LUR(
            product_feature="cool.beans",
            total=11,
            used=11,
            used_licenses=[{"booked": 11, "lead_host": "host1", "user_name": "user1"}],
        ),
        LUR(
            product_feature="limited.license",
            total=50,
            used=40,
            used_licenses=[{"booked": 40, "lead_host": "host1", "user_name": "user1"}],
        ),
    ]
    return inserts
