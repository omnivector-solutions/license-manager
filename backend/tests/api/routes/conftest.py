from pytest import fixture

from lm_backend.api.models import (
    Booking,
    Cluster,
    Configuration,
    Feature,
    Inventory,
    Job,
    LicenseServer,
    Product,
)


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
        },
        {
            "name": "Converge",
            "cluster_id": cluster_id,
            "grace_time": 60,
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
            "type": "flexlm",
        },
        {
            "config_id": configuration_id,
            "host": "licserv0002.com",
            "port": 2345,
            "type": "rlm",
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
            "type": "flexlm",
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
async def create_features(insert_objects, create_one_configuration, create_one_product):
    configuration_id = create_one_configuration[0].id
    product_id = create_one_product[0].id

    features_to_add = [
        {
            "name": "abaqus",
            "product_id": product_id,
            "config_id": configuration_id,
            "reserved": 0,
        },
        {
            "name": "converge_super",
            "product_id": product_id,
            "config_id": configuration_id,
            "reserved": 0,
        },
    ]

    inserted_features = await insert_objects(features_to_add, Feature)
    return inserted_features


@fixture
async def create_one_feature(insert_objects, create_one_configuration, create_one_product):
    configuration_id = create_one_configuration[0].id
    product_id = create_one_product[0].id

    feature_to_add = [
        {
            "name": "abaqus",
            "product_id": product_id,
            "config_id": configuration_id,
            "reserved": 0,
        },
    ]

    inserted_feature = await insert_objects(feature_to_add, Feature)
    return inserted_feature


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


@fixture
async def create_inventories(
    insert_objects,
    create_features,
):
    feature1_id = create_features[0].id
    feature2_id = create_features[1].id

    inventories_to_add = [
        {
            "feature_id": feature1_id,
            "total": 1000,
            "used": 250,
        },
        {
            "feature_id": feature2_id,
            "total": 1000,
            "used": 250,
        },
    ]

    inserted_inventories = await insert_objects(inventories_to_add, Inventory)
    return inserted_inventories


@fixture
async def create_one_inventory(insert_objects, create_one_feature):
    feature1_id = create_one_feature[0].id

    inventories_to_add = [
        {
            "feature_id": feature1_id,
            "total": 1000,
            "used": 250,
        },
    ]

    inserted_inventory = await insert_objects(inventories_to_add, Inventory)
    return inserted_inventory
