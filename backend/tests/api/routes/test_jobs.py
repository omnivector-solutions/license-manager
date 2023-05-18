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
    create_one_cluster,
    clean_up_database,
):
    cluster_id = create_one_cluster[0].id

    data = {
        "slurm_job_id": "123",
        "cluster_id": cluster_id,
        "username": "user",
        "lead_host": "test-host",
    }

    inject_security_header("owner1", Permissions.JOB_EDIT)
    response = await backend_client.post("/lm/jobs", json=data)
    assert response.status_code == 201

    stmt = select(Job).where(Job.slurm_job_id == data["slurm_job_id"])
    fetched = await read_object(stmt)

    assert fetched.slurm_job_id == data["slurm_job_id"]
    assert fetched.cluster_id == data["cluster_id"]
    assert fetched.username == data["username"]
    assert fetched.lead_host == data["lead_host"]


@mark.asyncio
async def test_get_all_jobs__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_jobs,
    clean_up_database,
):
    inject_security_header("owner1", Permissions.JOB_VIEW)
    response = await backend_client.get("/lm/jobs")

    assert response.status_code == 200

    response_jobs = response.json()
    assert response_jobs[0]["slurm_job_id"] == create_jobs[0].slurm_job_id
    assert response_jobs[0]["cluster_id"] == create_jobs[0].cluster_id
    assert response_jobs[0]["username"] == create_jobs[0].username
    assert response_jobs[0]["lead_host"] == create_jobs[0].lead_host

    assert response_jobs[1]["slurm_job_id"] == create_jobs[1].slurm_job_id
    assert response_jobs[1]["cluster_id"] == create_jobs[1].cluster_id
    assert response_jobs[1]["username"] == create_jobs[1].username
    assert response_jobs[1]["lead_host"] == create_jobs[1].lead_host


@mark.asyncio
async def test_get_all_jobs__with_search(
    backend_client: AsyncClient,
    inject_security_header,
    create_jobs,
    clean_up_database,
):
    inject_security_header("owner1", Permissions.JOB_VIEW)
    response = await backend_client.get(f"/lm/jobs/?search={create_jobs[0].slurm_job_id}")

    assert response.status_code == 200

    response_jobs = response.json()
    assert response_jobs[0]["slurm_job_id"] == create_jobs[0].slurm_job_id
    assert response_jobs[0]["cluster_id"] == create_jobs[0].cluster_id
    assert response_jobs[0]["username"] == create_jobs[0].username
    assert response_jobs[0]["lead_host"] == create_jobs[0].lead_host


@mark.asyncio
async def test_get_all_jobs__with_sort(
    backend_client: AsyncClient,
    inject_security_header,
    create_jobs,
    clean_up_database,
):

    inject_security_header("owner1", Permissions.JOB_VIEW)
    response = await backend_client.get("/lm/jobs/?sort_field=slurm_job_id&sort_ascending=false")

    assert response.status_code == 200

    response_jobs = response.json()
    assert response_jobs[0]["slurm_job_id"] == create_jobs[1].slurm_job_id
    assert response_jobs[0]["cluster_id"] == create_jobs[1].cluster_id
    assert response_jobs[0]["username"] == create_jobs[1].username
    assert response_jobs[0]["lead_host"] == create_jobs[1].lead_host

    assert response_jobs[1]["slurm_job_id"] == create_jobs[0].slurm_job_id
    assert response_jobs[1]["cluster_id"] == create_jobs[0].cluster_id
    assert response_jobs[1]["username"] == create_jobs[0].username
    assert response_jobs[1]["lead_host"] == create_jobs[0].lead_host


@mark.asyncio
async def test_get_job__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    clean_up_database,
):
    id = create_one_job[0].id

    inject_security_header("owner1", Permissions.JOB_VIEW)
    response = await backend_client.get(f"/lm/jobs/{id}")

    assert response.status_code == 200

    response_job = response.json()
    assert response_job["slurm_job_id"] == create_one_job[0].slurm_job_id
    assert response_job["cluster_id"] == create_one_job[0].cluster_id
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
    clean_up_database,
    id,
):
    inject_security_header("owner1", Permissions.JOB_VIEW)
    response = await backend_client.get(f"/lm/jobs/{id}")

    assert response.status_code == 404


@mark.asyncio
async def test_delete_job__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    read_object,
    clean_up_database,
):
    id = create_one_job[0].id

    inject_security_header("owner1", Permissions.JOB_EDIT)
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
    clean_up_database,
    id,
):
    inject_security_header("owner1", Permissions.JOB_EDIT)
    response = await backend_client.delete(f"/lm/jobs/{id}")

    assert response.status_code == 404


@mark.asyncio
async def test_delete_job_by_slurm_id__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    read_object,
    clean_up_database,
):
    slurm_job_id = create_one_job[0].slurm_job_id
    cluster_id = create_one_job[0].cluster_id

    inject_security_header("owner1", Permissions.JOB_EDIT)
    response = await backend_client.delete(f"/lm/jobs/slurm_job_id/{slurm_job_id}/cluster/{cluster_id}")

    assert response.status_code == 200
    stmt = select(Job).where(Job.slurm_job_id == slurm_job_id and Job.cluster_id == cluster_id)
    fetch_job = await read_object(stmt)

    assert fetch_job is None


@mark.parametrize(
    "slurm_job_id, cluster_id",
    [
        ("12345", 0),
        ("not-a-job-id", -1),
        ("non-existant-job-id", 999999999),
    ],
)
@mark.asyncio
async def test_delete_job_by_slurm_id__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    clean_up_database,
    slurm_job_id,
    cluster_id,
):
    inject_security_header("owner1", Permissions.JOB_EDIT)
    response = await backend_client.delete(f"/lm/jobs/slurm_job_id/{slurm_job_id}/cluster/{cluster_id}")

    assert response.status_code == 404


@mark.asyncio
async def test_read_job_by_slurm_id__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    clean_up_database,
):
    slurm_job_id = create_one_job[0].slurm_job_id
    cluster_id = create_one_job[0].cluster_id

    inject_security_header("owner1", Permissions.JOB_EDIT)
    response = await backend_client.get(f"/lm/jobs/slurm_job_id/{slurm_job_id}/cluster/{cluster_id}")

    assert response.status_code == 200

    response_job = response.json()
    assert response_job["slurm_job_id"] == create_one_job[0].slurm_job_id
    assert response_job["cluster_id"] == create_one_job[0].cluster_id
    assert response_job["username"] == create_one_job[0].username
    assert response_job["lead_host"] == create_one_job[0].lead_host


@mark.parametrize(
    "slurm_job_id, cluster_id",
    [
        ("12345", 0),
        ("not-a-job-id", -1),
        ("non-existant-job-id", 999999999),
    ],
)
@mark.asyncio
async def test_read_job_by_slurm_id__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    clean_up_database,
    slurm_job_id,
    cluster_id,
):
    inject_security_header("owner1", Permissions.JOB_VIEW)
    response = await backend_client.get(f"/lm/jobs/slurm_job_id/{slurm_job_id}/cluster/{cluster_id}")

    assert response.status_code == 404
