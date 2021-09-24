from pytest import fixture

from lm_backend.api_schemas import BookingRow, ConfigurationRow


@fixture
def some_config_rows():
    """
    Sample config_table row.
    """
    return [
        ConfigurationRow(
            id=1,
            product="hello",
            features=["world", "dolly"],
            license_servers=["bla"],
            license_server_type="test",
            grace_time=10,
        ),
        ConfigurationRow(
            id=2,
            product="cool",
            features=["beans"],
            license_servers=["bla"],
            license_server_type="test",
            grace_time=10,
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
        ),
        BookingRow(
            id=2,
            job_id="hellodolly",
            product_feature="hello.dolly",
            booked=11,
            config_id=1,
            lead_host="host1",
            user_name="user1",
        ),
        BookingRow(
            id=3,
            job_id="coolbeans",
            product_feature="cool.beans",
            booked=11,
            config_id=2,
            lead_host="host1",
            user_name="user1",
        ),
    ]