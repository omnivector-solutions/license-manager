from pytest import fixture

from lm_backend.api.models.booking import Booking
from lm_backend.api.models.cluster import Cluster
from lm_backend.api.models.configuration import Configuration
from lm_backend.api.models.feature import Feature
from lm_backend.api.models.job import Job
from lm_backend.api.models.license_server import LicenseServer
from lm_backend.api.models.product import Product


@fixture
async def create_clusters(insert_objects):
    clusters_to_add = [
        {
            "name": "Dummy Cluster",
            "client_id": "dummy",
        },
        {
            "name": "Dummy Cluster 2",
            "client_id": "dummy2",
        },
    ]
    inserted_clusters = await insert_objects(clusters_to_add, Cluster)
    return inserted_clusters


@fixture
async def create_one_cluster(insert_objects):
    cluster_to_add = [
        {
            "name": "Dummy Cluster",
            "client_id": "dummy",
        },
    ]
    inserted_cluster = await insert_objects(cluster_to_add, Cluster)
    return inserted_cluster


@fixture
async def create_configurations(insert_objects, create_one_cluster):
    cluster_id = create_one_cluster[0].id

    configurations_to_add = [
        {
            "name": "Abaqus",
            "cluster_id": cluster_id,
            "grace_time": 60,
            "type": "flexlm",
        },
        {
            "name": "Converge",
            "cluster_id": cluster_id,
            "grace_time": 60,
            "type": "rlm",
        },
    ]
    inserted_configurations = await insert_objects(configurations_to_add, Configuration)
    return inserted_configurations


@fixture
async def create_one_configuration(insert_objects, create_one_cluster):
    cluster_id = create_one_cluster[0].id

    configuration_to_add = [
        {
            "name": "Abaqus",
            "cluster_id": cluster_id,
            "grace_time": 60,
            "type": "flexlm",
        },
    ]

    inserted_configuration = await insert_objects(configuration_to_add, Configuration)
    return inserted_configuration


@fixture
async def create_license_servers(insert_objects, create_one_configuration):
    configuration_id = create_one_configuration[0].id

    license_servers_to_add = [
        {
            "config_id": configuration_id,
            "host": "licserv0001.com",
            "port": 1234,
        },
        {
            "config_id": configuration_id,
            "host": "licserv0002.com",
            "port": 2345,
        },
    ]

    inserted_license_servers = await insert_objects(license_servers_to_add, LicenseServer)
    return inserted_license_servers


@fixture
async def create_one_license_server(insert_objects, create_one_configuration):
    configuration_id = create_one_configuration[0].id

    license_server_to_add = [
        {
            "config_id": configuration_id,
            "host": "licserv0001.com",
            "port": 1234,
        },
    ]

    inserted_license_server = await insert_objects(license_server_to_add, LicenseServer)
    return inserted_license_server


@fixture
async def create_products(insert_objects):
    products_to_add = [
        {
            "name": "Abaqus",
        },
        {"name": "Converge"},
    ]

    inserted_products = await insert_objects(products_to_add, Product)
    return inserted_products


@fixture
async def create_one_product(insert_objects):
    product_to_add = [
        {
            "name": "Abaqus",
        }
    ]

    inserted_product = await insert_objects(product_to_add, Product)
    return inserted_product


@fixture
async def create_features(insert_objects, update_object, create_one_configuration, create_one_product):
    configuration_id = create_one_configuration[0].id
    product_id = create_one_product[0].id

    features_to_add = [
        {
            "name": "abaqus",
            "product_id": product_id,
            "config_id": configuration_id,
            "reserved": 100,
        },
        {
            "name": "converge_super",
            "product_id": product_id,
            "config_id": configuration_id,
            "reserved": 0,
        },
    ]

    inserted_features = await insert_objects(features_to_add, Feature)

    feature1_id = inserted_features[0].id
    feature2_id = inserted_features[1].id
    
    features_usage = [
        {
            "total": 1000,
            "used": 250,
        },
        {
            "total": 1000,
            "used": 250,
        },
    ]

    updated_features = []

    updated_features.append(update_object(id=feature1_id, total=features_usage[0]["total"], used=features_usage[0]["used"]))
    updated_features.append(update_object(id=feature2_id, total=features_usage[1]["total"], used=features_usage[1]["used"]))

    return updated_features


@fixture
async def create_one_feature(insert_objects, update_object, create_one_configuration, create_one_product):
    configuration_id = create_one_configuration[0].id
    product_id = create_one_product[0].id

    feature_to_add = [
        {
            "name": "abaqus",
            "product_id": product_id,
            "config_id": configuration_id,
            "reserved": 100,
        },
    ]

    inserted_feature = await insert_objects(feature_to_add, Feature)

    feature_id = inserted_feature[0].id
    feature_usage = {
        "total": 1000,
        "used": 250,
    }
    return update_object(id=feature_id, total=feature_usage["total"], used=feature_usage["used"])


@fixture
async def create_jobs(insert_objects, create_one_cluster):
    cluster_id = create_one_cluster[0].id
    jobs_to_add = [
        {
            "slurm_job_id": "123",
            "cluster_id": cluster_id,
            "username": "user",
            "lead_host": "test-host",
        },
        {
            "slurm_job_id": "234",
            "cluster_id": cluster_id,
            "username": "user2",
            "lead_host": "test-host2",
        },
    ]

    inserted_jobs = await insert_objects(jobs_to_add, Job)
    return inserted_jobs


@fixture
async def create_one_job(insert_objects, create_one_cluster):
    cluster_id = create_one_cluster[0].id
    job_to_add = [
        {
            "slurm_job_id": "123",
            "cluster_id": cluster_id,
            "username": "user",
            "lead_host": "test-host",
        },
    ]

    inserted_job = await insert_objects(job_to_add, Job)
    return inserted_job


@fixture
async def create_bookings(insert_objects, create_jobs, create_features):
    job1_id = create_jobs[0].id
    job2_id = create_jobs[1].id
    feature1_id = create_features[0].id
    feature2_id = create_features[1].id

    bookings_to_add = [
        {
            "job_id": job1_id,
            "feature_id": feature1_id,
            "quantity": 150,
        },
        {
            "job_id": job2_id,
            "feature_id": feature2_id,
            "quantity": 250,
        },
    ]

    inserted_bookings = await insert_objects(bookings_to_add, Booking)
    return inserted_bookings


@fixture
async def create_one_booking(insert_objects, create_one_job, create_one_feature):
    job_id = create_one_job[0].id
    feature_id = create_one_feature[0].id
    booking_to_add = [
        {
            "job_id": job_id,
            "feature_id": feature_id,
            "quantity": 150,
        },
    ]

    inserted_booking = await insert_objects(booking_to_add, Booking)
    return inserted_booking
