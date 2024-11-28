# License Manager API
The **License Manager API** provides a **RESTful API** where licenses and bookings are tracked.
The **License Manager Agent** uses this API to store the license usage information and to process the **Booking** requests.
The **License Manager CLI** interacts with this API to add new configurations and to check the usage information for each tracked license.

The **License Manager API** is also responsible for verifying if the **Booking** requests can be satisfied by accounting for **Bookings** already
made and the license usage in the **License Server**.

The **License Manager API** contains 6 distinct resources with interconnecting relationships.  
This means that some of the resources need to be created before others can be created as well.

``` mermaid
    erDiagram
        Bookings {
            int id pk
            int job_id pk
            int feature_id pk
            int quantity
        }
        Features {
            int id pk,fk
            str name
            int config_id pk
            int product_id pk
            int reserved
            int total
            int used
            int booked_total
        }
        Products {
            int id pk
            str name
        }
        Jobs {
            int id pk, fk
            str slurm_job_id
            str cluster_client_id
            str username
            str lead_host
        }
        Configurations {
            int id pk
            str name
            str cluster_client_id
            int grace_time
            enum[str] type
        }
        LicenseServers {
            int id pk
            int config_id fk
            str host
            int port
        }
        Jobs ||--o{ Bookings : ""
        Features ||--o{ Bookings : ""
        Products ||--o{ Features : ""
        Configurations ||--|{ Features : ""
        Configurations ||--|{ LicenseServers : ""
```

## Configurations
The **Configuration** resource holds the information for a set of **Features** that are available on the same **License Server**.

A **Configuration** represents the license configured in the **Slurm** cluster. The configuration is linked to the cluster by the **cluster_client_id** field.

The **License Manager Agent** instance running in the cluster will only reconcile the licenses configured for that cluster.

Since each **License Server** can have multiple licenses configured, the same **Configuration** can be used for each license present in the **License Server**.
The same command will be used to check the license usage for all the licenses under the same configuration.

The **Configuration** also defines the license type, the **License Server** host addresses and the **Grace Time** period.

The license type identifies the provider of the **License Server**.


The following **License Server types** are supported:

* FlexLM
* RLM
* LS-Dyna
* LM-X
* OLicense
* DSLS

## License Servers
The **License Server** resource represents the actual **License Server** where the license is installed.

A **License Server** has a host and a port, and each **Configuration** must have at least one **License Server** related to it.
The **Configuration** can cave multiple **License Servers** for redundancy, as long as they provide the same data.
Each **License Server** will be called, in order, if the previous one is not available.


## Products
The **Product** resource represents the product name of the license.

Each license is identified in the cluster as `product.feature@license_server_type`.
The **Product** is used to group the licenses that are under the same **License Server**

To create a **Feature**, a **Product** needs to be created first.


## Features
The **Feature** resource represents the licenses in the cluster.

Each **Feature** must be related to a **Configuration** and a **Product**.

The **reserved** value represents how many licenses should be reserved for usage in desktop applications. The amount of licenses reserved is not used by the cluster.

**License Manager Agent** polls the **License Server** to populate the **used** and **total** values.
The information stored includes the total number of licenses available, how many licenses are in use in the **License Server** and how many are booked.

The `/lm/features/by_client_id` endpoint extracts the **cluster_client_id** from the request and updates the feature for that cluster. This endpoint is needed since there can be multiple licenses with the same name in different clusters.

The `/lm/features/bulk` endpoint is used by the **License Manager Agent** to update the counters for multiple features with the same request.


## Jobs
The **Job** resource represents the jobs submitted to the cluster.

When a job is submitted to **Slurm**, it is intercepted by the **SlurmctldProlog** script, which creates a **Job** in the **License Manager API**.

Each **Job** can have multiple **Bookings** related to it, depending on the number of licenses requested by the job.

Once the job finishes, the **SlurmctldEpilog** deletes the job from the **License Manager API** , along with its **Bookings**.

Since the  `slurm_job_id` is not unique across clusters, each job is identified by the `cluster_client_id` alongside the `slurm_job_id`.

The endpoint `/lm/jobs/by_client_id` extracts the `cluster_client_id` from the request and returns the jobs that belong to the cluster.

The in the POST endpoint, the parameter `cluster_client_id` is optional. If it's not provided, the `cluster_client_id` is extracted from the request.


## Bookings
The **Booking** resource is responsible for Booking licenses for a specific job.

The **Booking** ensures the job will have enough licenses to be used when it requests them to the **License Server**.

Each **Booking** is related to a **Job**. The `job_id` parameter identifies the **Job** in the **License Manager API**, and is different from the `slurm_job_id`
that idenfies it in the cluster.

## Permissions
The **License Manager API** needs an authentication provider (OIDC) to work safely.

To manage permissions, the **License Manager API** uses the [Armasec](https://github.com/omnivector-solutions/armasec) library.
[Armasec](https://github.com/omnivector-solutions/armasec) documentation has getting started guides to configure **Keycloak** or **Auth0** as the OIDC provider.

The endpoints have granular permissions, and the user needs to have the correct set of permissions to access them.
Each endpoint has four permissions, for example:

* `license-manager:config:create`
* `license-manager:config:read`
* `license-manager:config:update`
* `license-manager:config:delete`

There's also the `license-manager:admin` permission, which allows access to all operations in all endpoints.

## Reference
The [reference](../reference/api.md) page contains the endpoints and schemas available.
