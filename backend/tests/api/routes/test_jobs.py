from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_backend.api.models.job import Job
from lm_backend.permissions import Permissions


@mark.asyncio
async def test_add_job__success(
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
):
    data = {
        "slurm_job_id": "123",
        "username": "user",
        "lead_host": "test-host",
        "bookings": [],
    }
    client_id = "dummy"

    inject_security_header("owner1@test.com", Permissions.JOB_EDIT, client_id=client_id)
    response = await backend_client.post("/lm/jobs", json=data)
    assert response.status_code == 201

    stmt = select(Job).where(Job.slurm_job_id == data["slurm_job_id"])
    fetched = await read_object(stmt)

    assert fetched.slurm_job_id == data["slurm_job_id"]
    assert fetched.cluster_client_id == client_id
    assert fetched.username == data["username"]
    assert fetched.lead_host == data["lead_host"]
    assert fetched.bookings == []


@mark.asyncio
async def test_add_job__fail_with_bad_client_id(
    backend_client: AsyncClient,
    inject_security_header,
):
    data = {
        "slurm_job_id": "123",
        "username": "user",
        "lead_host": "test-host",
        "bookings": [],
    }

    inject_security_header("owner1@test.com", Permissions.JOB_EDIT)
    response = await backend_client.post("/lm/jobs", json=data)
    assert response.status_code == 400


@mark.asyncio
async def test_add_job__with_bookings(
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_feature,
):
    feature_name = create_one_feature[0].name
    product_name = create_one_feature[0].product.name
    client_id = "dummy"

    data = {
        "slurm_job_id": "123",
        "username": "user",
        "lead_host": "test-host",
        "bookings": [{"product_feature": f"{product_name}.{feature_name}", "quantity": 50}],
    }

    inject_security_header("owner1@test.com", Permissions.JOB_EDIT, client_id=client_id)
    response = await backend_client.post("/lm/jobs", json=data)
    assert response.status_code == 201

    stmt = select(Job).where(Job.slurm_job_id == data["slurm_job_id"])
    fetched = await read_object(stmt)

    assert fetched.slurm_job_id == data["slurm_job_id"]
    assert fetched.cluster_client_id == client_id
    assert fetched.username == data["username"]
    assert fetched.lead_host == data["lead_host"]
    assert fetched.bookings[0].feature_id == create_one_feature[0].id
    assert fetched.bookings[0].quantity == data["bookings"][0]["quantity"]


@mark.asyncio
async def test_add_job__with_bookings__fail_with_overbooking(
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_feature,
):
    feature_name = create_one_feature[0].name
    product_name = create_one_feature[0].product.name
    client_id = "dummy"

    data = {
        "slurm_job_id": "123",
        "username": "user",
        "lead_host": "test-host",
        "bookings": [{"product_feature": f"{product_name}.{feature_name}", "quantity": 9999}],
    }

    inject_security_header("owner1@test.com", Permissions.JOB_EDIT, client_id=client_id)
    response = await backend_client.post("/lm/jobs", json=data)
    assert response.status_code == 409

    stmt = select(Job).where(Job.slurm_job_id == data["slurm_job_id"])
    fetched = await read_object(stmt)

    assert fetched is None


@mark.asyncio
async def test_get_all_jobs__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_jobs,
):
    inject_security_header("owner1@test.com", Permissions.JOB_VIEW)
    response = await backend_client.get("/lm/jobs")

    assert response.status_code == 200

    response_jobs = response.json()
    assert response_jobs[0]["slurm_job_id"] == create_jobs[0].slurm_job_id
    assert response_jobs[0]["cluster_client_id"] == create_jobs[0].cluster_client_id
    assert response_jobs[0]["username"] == create_jobs[0].username
    assert response_jobs[0]["lead_host"] == create_jobs[0].lead_host

    assert response_jobs[1]["slurm_job_id"] == create_jobs[1].slurm_job_id
    assert response_jobs[1]["cluster_client_id"] == create_jobs[1].cluster_client_id
    assert response_jobs[1]["username"] == create_jobs[1].username
    assert response_jobs[1]["lead_host"] == create_jobs[1].lead_host


@mark.asyncio
async def test_get_all_jobs__with_search(
    backend_client: AsyncClient,
    inject_security_header,
    create_jobs,
):
    inject_security_header("owner1@test.com", Permissions.JOB_VIEW)
    response = await backend_client.get(f"/lm/jobs?search={create_jobs[0].slurm_job_id}")

    assert response.status_code == 200

    response_jobs = response.json()
    assert response_jobs[0]["slurm_job_id"] == create_jobs[0].slurm_job_id
    assert response_jobs[0]["cluster_client_id"] == create_jobs[0].cluster_client_id
    assert response_jobs[0]["username"] == create_jobs[0].username
    assert response_jobs[0]["lead_host"] == create_jobs[0].lead_host


@mark.asyncio
async def test_get_all_jobs__with_sort(
    backend_client: AsyncClient,
    inject_security_header,
    create_jobs,
):

    inject_security_header("owner1@test.com", Permissions.JOB_VIEW)
    response = await backend_client.get("/lm/jobs?sort_field=slurm_job_id&sort_ascending=false")

    assert response.status_code == 200

    response_jobs = response.json()
    assert response_jobs[0]["slurm_job_id"] == create_jobs[1].slurm_job_id
    assert response_jobs[0]["cluster_client_id"] == create_jobs[1].cluster_client_id
    assert response_jobs[0]["username"] == create_jobs[1].username
    assert response_jobs[0]["lead_host"] == create_jobs[1].lead_host

    assert response_jobs[1]["slurm_job_id"] == create_jobs[0].slurm_job_id
    assert response_jobs[1]["cluster_client_id"] == create_jobs[0].cluster_client_id
    assert response_jobs[1]["username"] == create_jobs[0].username
    assert response_jobs[1]["lead_host"] == create_jobs[0].lead_host


@mark.asyncio
async def test_get_job__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
):
    id = create_one_job[0].id

    inject_security_header("owner1@test.com", Permissions.JOB_VIEW)
    response = await backend_client.get(f"/lm/jobs/{id}")

    assert response.status_code == 200

    response_job = response.json()
    assert response_job["slurm_job_id"] == create_one_job[0].slurm_job_id
    assert response_job["cluster_client_id"] == create_one_job[0].cluster_client_id
    assert response_job["username"] == create_one_job[0].username
    assert response_job["lead_host"] == create_one_job[0].lead_host


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_get_job__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    id,
):
    inject_security_header("owner1@test.com", Permissions.JOB_VIEW)
    response = await backend_client.get(f"/lm/jobs/{id}")

    assert response.status_code == 404


@mark.asyncio
async def test_delete_job__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    read_object,
):
    id = create_one_job[0].id

    inject_security_header("owner1@test.com", Permissions.JOB_EDIT)
    response = await backend_client.delete(f"/lm/jobs/{id}")

    assert response.status_code == 200
    stmt = select(Job).where(Job.id == id)
    fetch_job = await read_object(stmt)

    assert fetch_job is None


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_delete_job__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    id,
):
    inject_security_header("owner1@test.com", Permissions.JOB_EDIT)
    response = await backend_client.delete(f"/lm/jobs/{id}")

    assert response.status_code == 404


@mark.asyncio
async def test_delete_job_by_slurm_id__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    read_object,
):
    slurm_job_id = create_one_job[0].slurm_job_id
    cluster_client_id = create_one_job[0].cluster_client_id
    inject_security_header("owner@test1.com", Permissions.JOB_EDIT, client_id=cluster_client_id)
    response = await backend_client.delete(f"/lm/jobs/slurm_job_id/{slurm_job_id}")

    assert response.status_code == 200
    stmt = select(Job).where(Job.slurm_job_id == slurm_job_id and Job.cluster_client_id == cluster_client_id)
    fetch_job = await read_object(stmt)

    assert fetch_job is None


@mark.parametrize(
    "slurm_job_id",
    [
        ("12345"),
        ("not-a-job-id"),
        ("non-existant-job-id"),
    ],
)
@mark.asyncio
async def test_delete_job_by_slurm_id__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    slurm_job_id,
):
    cluster_client_id = create_one_job[0].cluster_client_id

    inject_security_header("owner1@test.com", Permissions.JOB_EDIT, client_id=cluster_client_id)
    response = await backend_client.delete(f"/lm/jobs/slurm_job_id/{slurm_job_id}")

    assert response.status_code == 404


@mark.asyncio
async def test_read_job_by_slurm_id__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
):
    slurm_job_id = create_one_job[0].slurm_job_id
    cluster_client_id = create_one_job[0].cluster_client_id

    inject_security_header("owner1@test.com", Permissions.JOB_VIEW, client_id=cluster_client_id)
    response = await backend_client.get(f"/lm/jobs/slurm_job_id/{slurm_job_id}")

    assert response.status_code == 200

    response_job = response.json()
    assert response_job["slurm_job_id"] == create_one_job[0].slurm_job_id
    assert response_job["cluster_client_id"] == create_one_job[0].cluster_client_id
    assert response_job["username"] == create_one_job[0].username
    assert response_job["lead_host"] == create_one_job[0].lead_host


@mark.parametrize(
    "slurm_job_id",
    [
        ("12345"),
        ("not-a-job-id"),
        ("non-existant-job-id"),
    ],
)
@mark.asyncio
async def test_read_job_by_slurm_id__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    slurm_job_id,
):
    cluster_client_id = create_one_job[0].cluster_client_id

    inject_security_header("owner1@test.com", Permissions.JOB_VIEW, client_id=cluster_client_id)
    response = await backend_client.get(f"/lm/jobs/slurm_job_id/{slurm_job_id}")

    assert response.status_code == 404
