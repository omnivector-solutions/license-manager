# License Manager Architecture
`License Manager` works in a client/server architecture, where the main components are the `Agent`, the `API` and the `CLI`.

The `License Manager Agent` is the component that syncs the local `Slurm` license counters with the License Server data.
It's also responsible for making `Booking` requests to the License Manager API when a job is submitted to Slurm.

`The License Manager API` provides a `RESTful API` where license usage and `Bookings` are tracked. The `License Manager Agent` uses this `API`
to store the license usage information and to process the `Booking` requests.

The `License Manager CLI` is an interface to interact with the `API` to add new license configurations and to check the usage information for each tracked license.


## License Manager Agent
`License Manager` is used to ensure that when a job is executed, there are enough free licenses for it to succeed. The `License Manager Agent` is the component that makes it possible.

The agent has two main functionalities:

* Sync the local `Slurm` license counters with the usage from the `License Server`

* Manage the license requests from jobs submitted to the cluster using `Bookings`.

Since the `Slurm` license counter doesn’t interact with the `License Servers`, `License Manager Agent` polls the data from the `License Servers` and updates the counters in `Slurm`.
Each cluster managed by `License Manager` has its own license counter linked to the `License Server`, enabling license sharing among clusters.

### Bookings
`License Manager` provides custom scripts for `SlurmctldProlog` and `SlurmctldEpilog`, executed when a job is submitted and when it finishes.

Each job submitted to Slurm that has the `license flag` will trigger the `PrologSlurmctld` script that makes a request to the `License Manager API`
to create a `Booking` for the needed licenses prior to the allocation of the job. The `Booking` ensures that the licenses are available for the job
to use by taking into consideration the licenses booked for other jobs and the license usage in the License Server.

If the `Booking` cannot be made, the job will be kept in the queue until there are enough licenses available to satisfy the `Booking` request.

To calculate if the license is available for use, the formula used is:

````
available = licenses booked + licenses used in License Server + licenses requested by job < total amount of licenses
````

The `Booking` will live until one of the following conditions are met:

1. When the `grace time` expires (defaults to 5 minutes, but can be configured)

2. When `License Manager` identifies that the license was already checked out

3. When the job finishes running

The `SlurmctldEpilog` script is responsible for deleting the `Booking` when the job finishes if it’s still in the `API`.
The other conditions are checked by the `Reconciliation`.

#### Deleting Bookings by Grace Time
A job can take some time to check out the license from the `License Server` after it is submitted to `Slurm`.
Thus, each license has a `grace time` period that is used to indicate how long a `Booking` will be retained.
After the `grace time` expires, the `Booking` is deleted. This means that the license was checked out from the
`License Server` and doesn't need a `Booking` anymore.

#### Deleting Bookings by matching
The output from each `License Server` supported by `License Manager` has two main sections:

* License information: `Used` and `Total` counters
* Usage: how many licenses each `User` is using and the `Lead Host` from where the request was made

The `Booking` from `License Manager` contains the same information as the usage section.

If there’s a match between a `Booking` and a `usage line` from the `License Server`, the `Booking` is deleted even if the `Grace Time` is not expired yet.
This prevents double booking the license, since License Manager would take into account the `Booking` and the usage when updating the total amount of licenses used.

### Reconciliation
For each license tracked by `License Manager`, the `License Manager Agent` will periodically poll the `License Servers` to get
the usage information and store it in the `License Manager API`. The `stat-interval` is the period of time
between each Reconciliation and can be configured in the `License Manager Agent` configuration file.

The `Reconciliation` is also triggered when the `SlurmctldProlog` and `SlurmctldEpilog` run.

The information in the `License Manager API` is used by the `Reconciliation` process to update the license counters in `Slurm`.

#### Slurm License Counters
The license counter in `Slurm` shows the total number of licenses, how many are in use, and how many are reserved.
The counter for licenses in use only accounts for licenses being used by jobs running in the cluster and can’t be edited manually.

The licenses can be used anywhere, such as other clusters and desktop applications sharing the same license pool, so the `Reconciliation`
syncs the counters in the cluster with the values in the `License Servers` to account for usage in other environments.

The main issue is that the `Used` counter is a read-only value.

#### Slurm Reservation
`Slurm` has the ability to reserve resources to be used by specific users. This can also be used to block resource usage during maintenance downtime, for example.

Due to the `Slurm` counters being immutable, `License Manager Agent` uses this feature to block the licenses that are already in use
in the `License Server`, which can be used in any environment. 

The `Reservation` mechanism should not be confused with the `Booking` created by the `SlurmctldProlog` in the `API`.

To calculate the number of licenses reserved, the following formula is used:

```
reserved = licenses used in License Server - licenses used by Slurm + licenses booked
```

This `Reservation` is not meant to be consumed by users nor jobs; it's only a representation of the licenses in use.

The `Reservation` is created by the user configured in the `License Manager Agent` configuration file. The user must
have a user account in the `Slurm` cluster and have `operator` privilege level to manage `Reservations`.

### License Manager Agent Workflow
Sequence diagram for the timed `Reconciliation`:

``` mermaid
    sequenceDiagram
        participant Slurm
        participant Reconciliation
        participant LicenseServer as License Server
        participant LMAPI as LM API

        %% Sequence begins
        Slurm->>Reconciliation: Timed Reconciliation
        Reconciliation->>LicenseServer: Access License Server
        LicenseServer-->>Reconciliation: Get updated counters
        Reconciliation->>LMAPI: Update API counters
        Reconciliation->>LMAPI: Clean Bookings by grace time and matching
        LMAPI-->>Reconciliation: Get new counters with Bookings deleted
        Reconciliation-->>Slurm: Update Reservation with license usage
```



Sequence diagram for when a job is submitted to `Slurm`:
``` mermaid
    sequenceDiagram
        participant Slurm
        participant Prolog
        participant Reconciliation
        participant LicenseServer as License Server
        participant LMAPI as LM API

        %% Sequence begins
        Slurm->>Prolog: Job is submitted
        Prolog->>Reconciliation: Forced Reconciliation
        Reconciliation->>LicenseServer: Access License Server
        LicenseServer-->>Reconciliation: Get updated counters
        Reconciliation->>LMAPI: Update API counters
        Reconciliation->>Slurm: Update Reservation with license usage
        Prolog->>LMAPI: Create Booking
        LMAPI-->>Prolog: Booking creation succeeded
        Slurm->>Slurm: Start job
        
        %% Timed Reconciliation starts
        Slurm->>Reconciliation: Timed Reconciliation
        Reconciliation->>LicenseServer: Access License Server
        LicenseServer-->>Reconciliation: Get updated counters
        Reconciliation->>LMAPI: Clean Bookings by grace time and matching
        LMAPI-->>Reconciliation: Keep Booking (not expired or not checked out yet)
        Reconciliation->>Slurm: Update Reservation with license usage

        %% Job checks out the license
        Slurm->>LicenseServer: Job checks out the license
        Slurm->>Reconciliation: Timed Reconciliation
        Reconciliation->>LicenseServer: Access License Server
        LicenseServer-->>Reconciliation: Get updated counters
        Reconciliation->>LMAPI: Clean Bookings by grace time and matching
        LMAPI-->>Reconciliation: Delete Booking (matched with a checked-out license)
        Reconciliation->>Slurm: Update Reservation with license usage
```

## License Manager API
The `License Manager API` provides a `RESTful API` where licenses and bookins are tracked.
The `License Manager Agent` uses this API to store the license usage information and to process the `Booking` requests.
The `License Manager CLI` interacts with this API to add new configurations and to check the usage information for each tracked license.

The `API` is also responsible for verifying if the `Booking` requests can be satisfied by accounting for `Bookings` already
made and the license usage in the `License Server`.

The `API` contains 6 entities that have relationship among them.
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
        
### Configurations
The `Configuration` resource holds the information for a set of `Features` that are available on the same `License Server`.

A `Configuration` is attached to a cluster and can have `n` `Features` attached to it.
It also defines the license type, the `License Server` host addresses and the `grace time` period.
The license type identifies the provider of the `License Server`.


The following `License Server types` are supported:

* FlexLM
* RLM
* LS-Dyna
* LM-X
* OLicense
* DSLS

Endpoints available:

* POST `/lm/configurations`
* GET `/lm/configurations`
* GET `/lm/configurations/by_client_id`
* GET `/lm/configurations/{id}`
* PUT `/lm/configurations/{id}`
* DEL `/lm/configurations/{id}`

The endpoint `by_client_id` extracts the `cluster_client_id` from the request and returns the configurations that belong to the cluster.

Payload example for POST:

``` json
{
    "name": "configuration-name",
    "cluster_client_id": "cluster-client-id", 
    "grace_time": 60,
    "type": "flexlm"
}
```

After creating a configuration, the License Servers and features can be added.

### License Servers
The `License Server` resource represents the actual `License Server` where the license is installed.

A `License Server` has a host and a port, and needs to be attached to a configuration.
Each configuration can have `n` `License Servers`, as long as they provide the same data (mirrored for redundancy).

Endpoints available:

* POST `/lm/license_servers`
* GET `/lm/license_servers`
* GET `/lm/license_servers/{id}`
* PUT `/lm/license_servers/{id}`
* DEL `/lm/license_servers/{id}`

Payload example for POST:

``` json
{
    "config_id": 1,
    "host": "licserv0001",
    "port": 1234
}
```


### Products
The `Product` resource represents the product name of the license.

Each license is identified as `product.feature@license_server_type`.
To create a `Feature`, a `Product` needs to be created first.

Endpoints available:

* POST `/lm/products`
* GET `/lm/products`
* GET `/lm/products/{id}`
* PUT `/lm/products/{id}`
* DEL `/lm/products/{id}`

Payload example for POST:

``` json
{
    "name": "abaqus"
}
```


### Features
The `Feature` resource represents the licenses in the cluster.

Each `Feature` is attached to a `Configuration` and a `Product`.

The feature has a `reserved` value, that represents how many licenses should be reserved for usage in desktop applications.
The amount of licenses reserved is not used by the cluster.

The `License Manager Agent` polls the `License Server` to populate the `used` and `total` values.
The information stored includes the total number of licenses available and how many licenses are in use.

Endpoints available:

* POST `/lm/features`
* POST `lm/features/bulk`
* GET `/lm/features`
* GET `/lm/features/{id}`
* PUT `/lm/features/{id}`
* PUT `/lm/features/by_client_id`
* DEL `/lm/features/{id}`

The endpoint `by_client_id` extracts the `cluster_client_id` from the request and updates the feature for that cluster.

This endpoint is needed since there can be multiple licenses with the same name in different clusters.

The endpoint `bulk` is used by the `License Manager Agent` to update the counters for multiple features with the same request.


Payload example for POST:

``` json
{
    "name": "abaqus",
    "product_id": 1,
    "config_id": 1,
    "reserved": 50,
}
```

### Jobs
The `Job` resource represents the jobs submitted to the cluster.

When a job is intercepted by the `PrologSlurmctld` script, the job is created automatically.

Each `Job` can have `n` `Bookings` attached to it.
If the job requires licenses, a `Booking` is created for each license.
Once the job finishes, the `EpilogSlurmctld` deletes the job from the `API` , along with its `Bookings`.

Since the `slurm_job_id` is not unique across clusters, each job is identified by the `cluster_client_id` alongside the `slurm_job_id`.

Endpoints available:

* POST `/lm/jobs`
* GET `/lm/jobs`
* GET `/lm/jobs/by_client_id`
* GET `/lm/jobs/{id}`
* GET `/lm/jobs/slurm_job_id/{slurm_job_id}`
* DEL `/lm/jobs/{id}`
* DEL `/lm/jobs/slurm_job_id/{slurm_job_id}`

The endpoint `by_client_id` extracts the `cluster_client_id` from the request and returns the jobs that belong to the cluster.

The in the POST endpoint, the parameter `cluster_client_id` is optional. If it's not provided, the `cluster_client_id` is extracted from the request.

Payload example for POST:

``` json
{
    "slurm_job_id": "123",
    "cluster_client_id": "cluster-client-id",
    "username": "user123",
    "lead_host": "host1"
}
```

### Bookings
The `Booking` resource is responsible for Booking licenses for a specific job.

The Booking ensures the job will have enough licenses to be used when the `grace time` is reached.
`License Manager Agent` stores the information about the Booking requests made by Slurm when the `PrologSlurmctld`
script is used.

Each `Booking` is attached to a `Job`. The `job_id` parameter identifies the job in the API, and is different from the `slurm_job_id`
that idenfies it in the cluster.

Endpoints available:

* POST `/lm/Bookings`
* GET `/lm/Bookings`
* GET `/lm/Bookings/{id}`
* DEL `/lm/Bookings/{id}`

Payload example for POST:

``` json
{
    "job_id": 1,
    "feature_id": 1,
    "quantity": 50
}
```

### Permissions
The `License Manager API` needs an authentication provider (OIDC) to manage the permissions for the users.

We recommend using the `Keycloak` as the OIDC provider, but any provider that supports the `OIDC` protocol can be used.

Each endpoint is protected using [Armasec](https://github.com/omnivector-solutions/armasec), which manages the permissions
needed to access each endpoint. The permissions must be available as a claim in the JWT token.

The permissions are granular for each endpoint, and the user needs to have the correct permissions to access the endpoint.
Each endpoint has four permissions, for example:

* `license-manager:config:create`
* `license-manager:config:read`
* `license-manager:config:update`
* `license-manager:config:delete`

There's also the `license-manager:admin` permission, which allows access to all operations in all endpoints.

## License Manager CLI
The `License Manager CLI` is a client to interact with the `License Manager API`.

It can be used to add new configurations to the API and to check the usage information for each tracked license.

The `Jobs` and `Bookings` are read only. The remaining resources can be edited by users with permission to do so.

### Global commands
| **Command** | **Description** |
| ----------- | ----------------|
| lm-cli login | Generate a URL for logging in via browser |
| lm-cli show-token | Print your access token (created after logging in) |
| lm-cli logout | Logout and remove your access token |

### Configuration commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli configurations list | List all configurations |
| lm-cli configurations list<br>--search **<search string\>** | Search configurations with the specified string |
| lm-cli configurations list<br>--sort-field **<sort field\>** | Sort configurations by the specified field |
| lm-cli configurations list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>** | Sort configurations by the specified order |
| lm-cli configurations get-one<br>--id **<configuration id\>** | List the configuration with the specified id |
| lm-cli configurations create<br>--name **<configuration name\>**<br>--cluster-client-id **<OIDC client_id of the cluster where the configuration applies\>**<br>--grace-time **<grace time in seconds\>**<br>--license-server-type **<License Server type\>** | Create a new configuration |
| lm-cli configurations delete<br>--id **<id to delete\>** | Delete the configuration with the specified id |

### License server commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli license-servers list | List all License Servers |
| lm-cli license-servers list<br>--search **<search string\>** | Search License Servers with the specified string |
| lm-cli license-servers list<br>--sort-field **<sort field\>** | Sort License Servers by the specified field |
| lm-cli license-servers list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>** | Sort License Servers by the specified order |
| lm-cli license-servers get-one<br>--id **<License Server id\>** | List the License Server with the specified id |
| lm-cli license-servers create<br>--config-id **<id of the configuration to add the License Server\>**<br>--host **<hostname of the License Server\>**<br>--port **<port of the License Server\>** | Create a new License Server |
| lm-cli license-servers delete<br>--id **<id to delete\>** | Delete the License Server with the specified id    |

### Product commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli products list | List all products |
| lm-cli products list<br>--search **<search string\>** | Search products with the specified string |
| lm-cli products list<br>--sort-field **<sort field\>** | Sort products by the specified field |
| lm-cli products list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>** | Sort products by the specified order |
| lm-cli products get-one<br>--id **<product id\>** | List the product with the specified id |
| lm-cli products create<br>--name **<product name\>** | Create a new product |
| lm-cli products delete<br>--id **<id to delete\>** | Delete the product with the specified id |

### Feature commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli features list | List all features |
| lm-cli features list<br>--search **<search string\>** | Search features with the specified string |
| lm-cli features list<br>--sort-field **<sort field\>** | Sort features by the specified field |
| lm-cli features list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>** | Sort features by the specified order |
| lm-cli features get-one<br>--id **<feature id\>** | List the feature with the specified id |
| lm-cli features create<br>--name **<feature name\>**<br>--product-id **<id of the product of the license\>**<br>--config-id **<id of the configuration of the license\>**<br>--reserved **<how many licenses should be reserved for desktop environments\>** | Create a new feature |
| lm-cli features delete<br>--id **<id to delete\>** | Delete the feature with the specified id |

### Job commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli jobs list | List all jobs |
| lm-cli jobs list<br>--search **<search string\>** | Search jobs with the specified string |
| lm-cli jobs list<br>--sort-field **<sort field\>** | Sort jobs by the specified field |
| lm-cli jobs list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>** | Sort jobs by the specified order |

### Booking commands
| **Command** | **Description** |
| ----------- | --------------- |
| lm-cli Bookings list | List all Bookings |
| lm-cli Bookings list<br>--search **<search string\>** | Search Bookings with the specified string |
| lm-cli Bookings list<br>--sort-field **<sort field\>** | Sort Bookings by the specified field |
| lm-cli Bookings list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>**| Sort Bookings by the specified order |
