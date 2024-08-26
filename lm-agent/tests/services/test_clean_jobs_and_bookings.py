from collections import defaultdict

from pytest import mark
from unittest import mock

from lm_agent.services.clean_jobs_and_bookings import (
    extract_bookings_from_job,
    extract_usages_from_report,
    get_bookings_mapping,
    get_usages_mapping,
    clean_bookings_by_usage,
    get_cluster_grace_times,
    get_greatest_grace_time_for_job,
    clean_jobs_without_bookings,
    clean_jobs_no_longer_running,
    clean_jobs_by_grace_time,
    clean_jobs_and_bookings,
)
from lm_agent.models import (
    JobSchema,
    BookingSchema,
    ExtractedBookingSchema,
    ExtractedUsageSchema,
    LicenseReportItem,
)


def test_get_cluster_grace_times(parsed_configurations):
    """
    Test that get_cluster_grace_times generates a dict with the grace time for each feature_id.
    """
    expected_grace_times = {1: 60, 2: 123}

    result = get_cluster_grace_times(parsed_configurations)
    assert result == expected_grace_times


def test__get_greatest_grace_time_for_job(parsed_jobs):
    """
    Test if the function really returns the greatest value for the grace_time.
    """
    grace_times = {
        1: 10,
        2: 20,
    }
    job_bookings = parsed_jobs[0].bookings
    expected_result = 20

    result = get_greatest_grace_time_for_job(grace_times, job_bookings)
    assert result == expected_result


@mark.parametrize(
    "parsed_job,extracted_bookings",
    [
        (
            "one_parsed_job",
            [
                ExtractedBookingSchema(
                    booking_id=1,
                    job_id=1,
                    slurm_job_id="123",
                    username="user1",
                    lead_host="host1",
                    feature_id=1,
                    quantity=12,
                ),
                ExtractedBookingSchema(
                    booking_id=2,
                    job_id=1,
                    slurm_job_id="123",
                    username="user1",
                    lead_host="host1",
                    feature_id=2,
                    quantity=50,
                ),
            ],
        ),
        (
            "another_parsed_job",
            [
                ExtractedBookingSchema(
                    booking_id=3,
                    job_id=2,
                    slurm_job_id="456",
                    username="user2",
                    lead_host="host2",
                    feature_id=4,
                    quantity=15,
                ),
                ExtractedBookingSchema(
                    booking_id=4,
                    job_id=2,
                    slurm_job_id="456",
                    username="user2",
                    lead_host="host2",
                    feature_id=7,
                    quantity=25,
                ),
            ],
        ),
    ],
)
def test__extract_bookings_from_job(parsed_job, extracted_bookings, request):
    """
    Test that the bookings can be extrated from a job.
    """
    parsed_job = request.getfixturevalue(parsed_job)

    assert extract_bookings_from_job(parsed_job) == extracted_bookings


@mark.parametrize(
    "report_item,extracted_usages",
    [
        (
            "one_report_item",
            [
                ExtractedUsageSchema(feature_id=1, username="user1", lead_host="host1", quantity=100),
            ],
        ),
        (
            "another_report_item",
            [
                ExtractedUsageSchema(feature_id=2, username="user2", lead_host="host2", quantity=10),
            ],
        ),
    ],
)
def test__extract_usages_from_report(report_item, extracted_usages, request):
    """
    Test that the usages can be extracted from a report item.
    """
    report_item = request.getfixturevalue(report_item)

    assert extract_usages_from_report(report_item) == extracted_usages


def test_get_bookings_mapping(parsed_jobs):
    """
    Test tha the bookings can be mapped by the required information.
    """
    result = defaultdict(
        list,
        {
            (1, "user1", "host1", 100): [
                ExtractedBookingSchema(
                    booking_id=1,
                    job_id=1,
                    slurm_job_id="123",
                    username="user1",
                    lead_host="host1",
                    feature_id=1,
                    quantity=100,
                )
            ],
            (2, "user1", "host1", 50): [
                ExtractedBookingSchema(
                    booking_id=2,
                    job_id=1,
                    slurm_job_id="123",
                    username="user1",
                    lead_host="host1",
                    feature_id=2,
                    quantity=50,
                )
            ],
            (1, "user2", "host2", 15): [
                ExtractedBookingSchema(
                    booking_id=3,
                    job_id=2,
                    slurm_job_id="456",
                    username="user2",
                    lead_host="host2",
                    feature_id=1,
                    quantity=15,
                )
            ],
            (2, "user2", "host2", 25): [
                ExtractedBookingSchema(
                    booking_id=4,
                    job_id=2,
                    slurm_job_id="456",
                    username="user2",
                    lead_host="host2",
                    feature_id=2,
                    quantity=25,
                )
            ],
            (1, "user3", "host3", 5): [
                ExtractedBookingSchema(
                    booking_id=14,
                    job_id=3,
                    slurm_job_id="789",
                    username="user3",
                    lead_host="host3",
                    feature_id=1,
                    quantity=5,
                )
            ],
            (2, "user3", "host3", 17): [
                ExtractedBookingSchema(
                    booking_id=15,
                    job_id=3,
                    slurm_job_id="789",
                    username="user3",
                    lead_host="host3",
                    feature_id=2,
                    quantity=17,
                )
            ],
        },
    )

    assert get_bookings_mapping(parsed_jobs) == result


def test__get_usages_mapping(parsed_report_items):
    """
    Test that the usages can be mapped by the required information.
    """
    result = defaultdict(
        list,
        {
            (1, "user1", "host1", 100): [
                ExtractedUsageSchema(feature_id=1, username="user1", lead_host="host1", quantity=100)
            ],
            (2, "user2", "host2", 10): [
                ExtractedUsageSchema(feature_id=2, username="user2", lead_host="host2", quantity=10)
            ],
        },
    )

    assert get_usages_mapping(parsed_report_items) == result


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_job_by_slurm_job_id")
async def test__clean_jobs_without_bookings__removes_job(
    remove_job_mock, one_parsed_job, parsed_job_without_bookings
):
    """
    Test that the function removes the job when there are no bookings in it.
    """
    cluster_jobs = [one_parsed_job, parsed_job_without_bookings]

    remaining_jobs_with_bookings = await clean_jobs_without_bookings(cluster_jobs)

    remove_job_mock.assert_called_once_with(parsed_job_without_bookings.slurm_job_id)
    assert remaining_jobs_with_bookings == [one_parsed_job]


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_job_by_slurm_job_id")
async def test__clean_jobs_without_bookings__no_jobs_to_remove(remove_job_mock, one_parsed_job):
    """
    Test that the function doesn't remove any job when all jobs have bookings.
    """
    cluster_jobs = [one_parsed_job]

    remaining_jobs_with_bookings = await clean_jobs_without_bookings(cluster_jobs)

    remove_job_mock.assert_not_called()
    assert remaining_jobs_with_bookings == cluster_jobs


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_job_by_slurm_job_id")
async def test__clean_jobs_no_longer_running__not_running(remove_job_by_slurm_job_id_mock, parsed_jobs):
    """
    Check that the jobs that aren't running are cleaned.
    """
    squeue_result = [
        {"job_id": 123, "state": "RUNNING"},
        {"job_id": 456, "state": "COMPLETED"},
        {"job_id": 789, "state": "SUSPENDED"},
    ]

    remaining_jobs_with_bookings = await clean_jobs_no_longer_running(parsed_jobs, squeue_result)

    remove_job_by_slurm_job_id_mock.call_count == 2
    remove_job_by_slurm_job_id_mock.assert_has_calls([mock.call("456"), mock.call("789")])
    assert remaining_jobs_with_bookings == [parsed_jobs[0]]


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_job_by_slurm_job_id")
async def test__clean_jobs_no_longer_running__not_in_squeue(remove_job_by_slurm_job_id_mock, parsed_jobs):
    """
    Check that the jobs that aren't in the squeue result are cleaned.
    """
    squeue_result = [
        {"job_id": 123, "state": "RUNNING"},
    ]

    remaining_jobs_with_bookings = await clean_jobs_no_longer_running(parsed_jobs, squeue_result)

    remove_job_by_slurm_job_id_mock.call_count == 2
    remove_job_by_slurm_job_id_mock.assert_has_calls([mock.call("456"), mock.call("789")])
    assert remaining_jobs_with_bookings == [parsed_jobs[0]]


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_job_by_slurm_job_id")
async def test__clean_jobs_no_longer_running__no_squeue_result(remove_job_by_slurm_job_id_mock, parsed_jobs):
    """
    Check that all jobs are cleaned if there are no jobs in the squeue result.
    """
    squeue_result = []

    remaining_jobs_with_bookings = await clean_jobs_no_longer_running(parsed_jobs, squeue_result)

    remove_job_by_slurm_job_id_mock.call_count == 3
    remove_job_by_slurm_job_id_mock.assert_has_calls([mock.call("123"), mock.call("456"), mock.call("789")])
    assert remaining_jobs_with_bookings == []


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_job_by_slurm_job_id")
async def test__clean_jobs_by_grace_time__grace_time_expired(
    remove_job_by_slurm_job_id_mock,
    parsed_jobs,
):
    """
    Check that the job is cleaned when the running time is greater than grace_time.
    """
    slurm_job_id = "123"

    squeue_result = [
        {
            "job_id": 123,
            "run_time_in_seconds": 300,
            "state": "RUNNING",
        }
    ]
    grace_times = {1: 10, 2: 20, 4: 10, 7: 20}

    remaining_jobs = await clean_jobs_by_grace_time(parsed_jobs, squeue_result, grace_times)

    remove_job_by_slurm_job_id_mock.assert_awaited_once_with(slurm_job_id)
    assert len(remaining_jobs) == 2


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_job_by_slurm_job_id")
async def test__clean_jobs_by_grace_time__within_grace_time(
    remove_job_by_slurm_job_id_mock,
    parsed_jobs,
):
    """
    Check that the job is not cleaned when the running time is within the grace_time.
    """
    squeue_result = [
        {
            "job_id": 123,
            "run_time_in_seconds": 300,
            "state": "RUNNING",
        }
    ]
    grace_times = {1: 1000, 2: 3000, 4: 500, 7: 1500}

    remaining_jobs = await clean_jobs_by_grace_time(parsed_jobs, squeue_result, grace_times)

    remove_job_by_slurm_job_id_mock.assert_not_called()
    assert remaining_jobs == parsed_jobs


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_job_by_slurm_job_id")
async def test__clean_jobs_by_grace_time__no_jobs(
    remove_job_by_slurm_job_id_mock,
):
    """
    Check that the function doesn't do anything when there are no jobs.
    """
    squeue_result = []
    grace_times = {1: 1000, 2: 3000}

    remaining_jobs = await clean_jobs_by_grace_time([], squeue_result, grace_times)

    remove_job_by_slurm_job_id_mock.assert_not_called()
    assert remaining_jobs == []


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_booking")
async def test__clean_bookings_by_usage__only_one_booking(remove_bookings_mock):
    """
    Test that the bookings can be cleaned by usage when there is only one booking.
    """
    cluster_jobs = [
        JobSchema(
            id=1,
            slurm_job_id="123",
            cluster_client_id="dummy",
            username="user1",
            lead_host="host1",
            bookings=[
                BookingSchema(id=1, job_id=1, feature_id=1, quantity=12),
            ],
        ),
    ]

    report_items = [
        LicenseReportItem(
            feature_id=1,
            product_feature="product.feature",
            used=24,
            total=100,
            uses=[
                {"username": "user1", "lead_host": "host1", "booked": 12},
                {"username": "user2", "lead_host": "host2", "booked": 12},
            ],
        )
    ]

    await clean_bookings_by_usage(cluster_jobs, report_items)

    remove_bookings_mock.assert_called_once_with(1)


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_booking")
async def test__clean_bookings_by_usage__multiple_bookings(remove_bookings_mock):
    cluster_jobs = [
        JobSchema(
            id=1,
            slurm_job_id="123",
            cluster_client_id="dummy",
            username="user1",
            lead_host="host1",
            bookings=[
                BookingSchema(id=1, job_id=1, feature_id=1, quantity=12),
                BookingSchema(id=2, job_id=1, feature_id=2, quantity=50),
            ],
        ),
    ]

    report_items = [
        LicenseReportItem(
            feature_id=1,
            product_feature="product1.feature1",
            used=24,
            total=100,
            uses=[
                {"username": "user1", "lead_host": "host1", "booked": 12},
            ],
        ),
        LicenseReportItem(
            feature_id=2,
            product_feature="product2.feature2",
            used=50,
            total=100,
            uses=[
                {"username": "user1", "lead_host": "host1", "booked": 50},
            ],
        ),
    ]

    await clean_bookings_by_usage(cluster_jobs, report_items)

    remove_bookings_mock.assert_has_calls([mock.call(1), mock.call(2)])


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_booking")
async def test__clean_bookings_by_usage__multiple_jobs(remove_bookings_mock):
    cluster_jobs = [
        JobSchema(
            id=1,
            slurm_job_id="123",
            cluster_client_id="dummy",
            username="user1",
            lead_host="host1",
            bookings=[
                BookingSchema(id=1, job_id=1, feature_id=1, quantity=12),
            ],
        ),
        JobSchema(
            id=2,
            slurm_job_id="456",
            cluster_client_id="dummy",
            username="user2",
            lead_host="host2",
            bookings=[
                BookingSchema(id=2, job_id=2, feature_id=1, quantity=50),
            ],
        ),
    ]

    report_items = [
        LicenseReportItem(
            feature_id=1,
            product_feature="product.feature",
            used=24,
            total=100,
            uses=[
                {"username": "user1", "lead_host": "host1", "booked": 12},
                {"username": "user2", "lead_host": "host2", "booked": 50},
            ],
        ),
    ]

    await clean_bookings_by_usage(cluster_jobs, report_items)

    remove_bookings_mock.assert_has_calls([mock.call(1), mock.call(2)])


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_booking")
async def test__clean_bookings_by_usage__multiple_bookings_with_same_information(remove_bookings_mock):
    cluster_jobs = [
        JobSchema(
            id=1,
            slurm_job_id="123",
            cluster_client_id="dummy",
            username="user1",
            lead_host="host1",
            bookings=[
                BookingSchema(id=1, job_id=1, feature_id=1, quantity=12),
            ],
        ),
        JobSchema(
            id=2,
            slurm_job_id="234",
            cluster_client_id="dummy",
            username="user1",
            lead_host="host1",
            bookings=[
                BookingSchema(id=2, job_id=2, feature_id=1, quantity=12),
            ],
        ),
    ]

    report_items = [
        LicenseReportItem(
            feature_id=1,
            product_feature="product.feature",
            used=24,
            total=100,
            uses=[
                {"username": "user1", "lead_host": "host1", "booked": 12},
                {"username": "user1", "lead_host": "host1", "booked": 12},
            ],
        ),
    ]

    await clean_bookings_by_usage(cluster_jobs, report_items)

    remove_bookings_mock.assert_has_calls([mock.call(1), mock.call(2)])


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_booking")
async def test__clean_bookings_by_usage__more_bookings_than_usage(remove_booking_mock):
    cluster_jobs = [
        JobSchema(
            id=1,
            slurm_job_id="123",
            cluster_client_id="dummy",
            username="user1",
            lead_host="host1",
            bookings=[
                BookingSchema(id=1, job_id=1, feature_id=1, quantity=12),
            ],
        ),
        JobSchema(
            id=2,
            slurm_job_id="234",
            cluster_client_id="dummy",
            username="user1",
            lead_host="host1",
            bookings=[
                BookingSchema(id=2, job_id=2, feature_id=1, quantity=12),
            ],
        ),
    ]

    report_items = [
        LicenseReportItem(
            feature_id=1,
            product_feature="product.feature",
            used=12,
            total=100,
            uses=[
                {"username": "user1", "lead_host": "host1", "booked": 12},
            ],
        ),
    ]

    await clean_bookings_by_usage(cluster_jobs, report_items)

    remove_booking_mock.assert_not_called()


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_booking")
async def test__clean_bookings_by_usage__more_usages_than_bookings(remove_booking_mock):
    cluster_jobs = [
        JobSchema(
            id=1,
            slurm_job_id="123",
            cluster_client_id="dummy",
            username="user1",
            lead_host="host1",
            bookings=[
                BookingSchema(id=1, job_id=1, feature_id=1, quantity=12),
            ],
        ),
    ]

    report_items = [
        LicenseReportItem(
            feature_id=1,
            product_feature="product.feature",
            used=24,
            total=100,
            uses=[
                {"username": "user1", "lead_host": "host1", "booked": 12},
                {"username": "user1", "lead_host": "host1", "booked": 12},
            ],
        ),
    ]

    await clean_bookings_by_usage(cluster_jobs, report_items)

    remove_booking_mock.assert_not_called()


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_booking")
async def test__clean_bookings_by_usage__no_bookings(remove_booking_mock):
    cluster_jobs = [
        JobSchema(
            id=1,
            slurm_job_id="123",
            cluster_client_id="dummy",
            username="user1",
            lead_host="host1",
            bookings=[],
        ),
    ]

    report_items = [
        LicenseReportItem(
            feature_id=1,
            product_feature="product1.feature1",
            used=24,
            total=100,
            uses=[
                {"username": "user1", "lead_host": "host1", "booked": 12},
            ],
        ),
        LicenseReportItem(
            feature_id=2,
            product_feature="product2.feature2",
            used=50,
            total=100,
            uses=[
                {"username": "user1", "lead_host": "host1", "booked": 50},
            ],
        ),
    ]

    await clean_bookings_by_usage(cluster_jobs, report_items)

    remove_booking_mock.assert_not_called()


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_job_by_slurm_job_id")
async def test__clean_jobs_and_bookings__remove_jobs_without_bookings(
    remove_job_by_slurm_job_id_mock,
    parsed_configurations,
    parsed_report_items,
    one_parsed_job,
    parsed_job_without_bookings,
):
    cluster_jobs = [
        one_parsed_job,
        parsed_job_without_bookings,
    ]

    squeue_result = [
        {"job_id": 123, "run_time_in_seconds": 15, "state": "RUNNING"},
        {"job_id": 789, "run_time_in_seconds": 30, "state": "RUNNING"},
    ]

    await clean_jobs_and_bookings(parsed_configurations, cluster_jobs, squeue_result, parsed_report_items)

    remove_job_by_slurm_job_id_mock.assert_called_once_with("789")


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_job_by_slurm_job_id")
async def test__clean_jobs_and_bookings__remove_jobs_no_longer_running(
    remove_job_by_slurm_job_id_mock, parsed_configurations, parsed_report_items, parsed_jobs
):
    squeue_result = [
        {"job_id": 456, "run_time_in_seconds": 15, "state": "RUNNING"},
        {"job_id": 789, "run_time_in_seconds": 30, "state": "RUNNING"},
    ]

    await clean_jobs_and_bookings(parsed_configurations, parsed_jobs, squeue_result, parsed_report_items)

    remove_job_by_slurm_job_id_mock.assert_called_once_with("123")


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_job_by_slurm_job_id")
async def test__clean_jobs_and_bookings__clean_jobs_by_grace_time(
    remove_job_by_slurm_job_id_mock, parsed_configurations, parsed_report_items, parsed_jobs
):
    squeue_result = [
        {"job_id": 123, "run_time_in_seconds": 300, "state": "RUNNING"},
        {"job_id": 456, "run_time_in_seconds": 30, "state": "RUNNING"},
        {"job_id": 789, "run_time_in_seconds": 30, "state": "RUNNING"},
    ]

    await clean_jobs_and_bookings(parsed_configurations, parsed_jobs, squeue_result, parsed_report_items)

    remove_job_by_slurm_job_id_mock.assert_called_once_with("123")


@mark.asyncio
@mock.patch("lm_agent.services.clean_jobs_and_bookings.remove_booking")
async def test__clean_jobs_and_bookings__clean_bookings_by_usage(
    remove_booking_mock, parsed_configurations, parsed_report_items, parsed_jobs
):
    squeue_result = [
        {"job_id": 123, "run_time_in_seconds": 15, "state": "RUNNING"},
        {"job_id": 456, "run_time_in_seconds": 30, "state": "RUNNING"},
        {"job_id": 789, "run_time_in_seconds": 30, "state": "RUNNING"},
    ]

    await clean_jobs_and_bookings(parsed_configurations, parsed_jobs, squeue_result, parsed_report_items)

    remove_booking_mock.assert_called_once_with(1)
