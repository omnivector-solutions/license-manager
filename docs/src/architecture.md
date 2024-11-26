# License Manager Architecture

## Overview
**License Manager** works in a client/server architecture, where the main components are the **Agent**, the **API** and the **CLI**.

The **License Manager Agent** is the component that syncs the local **Slurm** license counters with the **License Server** data.
It's also responsible for making **Booking** requests to the **License Manager API** when a job is submitted to **Slurm**.

The **License Manager API** provides a **RESTful API** where license usage and **Bookings** are tracked. The **License Manager Agent** uses this **API**
to store the license usage information and to process the **Booking** requests.

The **License Manager CLI** provides an interface for managing license **Configurations** and retrieving usage information for tracked licenses via the **License Manager API**.  


## License Manager Agent
The **License Manager Agent** is the key component that ensures jobs have enough free licenses to execute successfully.
Deployed on the **Slurm** cluster, this agent works in conjunction with the **License Manager API** to track license usage and prevent job failures due to insufficient licenses.  

The agent has two main functionalities:

* Sync the local **Slurm** license counters with the usage from the **License Server**

* Manage the license requests from jobs submitted to the cluster using **Bookings**

Since the **Slurm** license counter doesn't directly interact with **License Servers**, the **License Manager Agent** actively polls the servers for data. Then it updates the corresponding counters in **Slurm**.
Each cluster managed by **License Manager** has a dedicated license counter linked to the **License Server**. This configuration allows for license sharing across multiple clusters.

### Bookings
**License Manager** provides custom scripts for **SlurmctldProlog** and **SlurmctldEpilog** that are executed when a job is submitted and when it finishes.

When submitting a job to **Slurm**, if the **sbatch** directive for requesting licenses (`-L` or `--licenses`) is included in the job script, the **SlurmctldProlog** will intercept the job and make a **Booking** request to the **License Manager API**.
The **Booking** reserves the needed licenses prior to the allocation of the job. The **Booking** ensures that the licenses are available for the job to use by taking into consideration the licenses booked for other jobs and the license usage in the **License Server**.

If the **Booking** cannot be made, the job will be kept in the queue until there are enough licenses available to satisfy the **Booking** request.

To calculate if the license is available for use, the formula used is:

$$
\begin{aligned}
\text{available} &= \text{licenses booked} \\
&+ \text{licenses used in License Server} \\
&+ \text{licenses requested by job} \\
&< \text{total amount of licenses}
\end{aligned}
$$

The **Booking** will live until one of the following conditions are met:

* When the **Grace Time** expires:

   The **Grace Time** defaults to 5 minutes, but it can be configured by setting an environment variable in the **Agent**'s configuration file.
   **Grace time** expiration is checked by the **Reconcilliation** process.
   
* When **License Manager** identifies that the license was already checked out:

   The license is checked-out when the application is granted the licenses by the **License Server**.
   The **Reconcilliation** process checks for matches between the active **Bookings** and the licenses checked out in the **License Server**
   to check if the **Booking** can be deleted.
   
* When the job finishes running:

   The **SlurmctldEpilog** script is executed when a job finishes. This script will  
   delete the booking if the **License Manager API** is still tracking the booking, which happens when the job finishes before the expiration of the **Grace Time**.

#### Deleting Bookings by Grace Time
Depending on the HPC application used by a job, it may take some time to check out the license from the **License Server** after it is submitted to **Slurm**.
It will take longer for jobs that have multiple setup steps before actually starting the application that requires the license.

Thus, each license has a **Grace Time** period that is used to indicate how long a **Booking** will be retained.

After the **Grace Time** expires, the **Booking** is deleted. This means that the license was checked out from the
**License Server** and doesn't need a **Booking** anymore.

If the **Booking** is not deleted once the license is checked out, **License Manager** would account for usage twice: once for the **Booking** and once for the actual usage. This double booking issue is mitigated by the **Grace Time** and by matching the **Booking** with the usage from the **License Server**.

#### Deleting Bookings by matching
**License Manager** parses output from each **License Server** to gather information into two main sections:  

* License information: **Used** and **Total** counters

* Usage: how many licenses each **User** is using and the **Lead Host** from where the request was made

The **Booking** from **License Manager** contains the same information as the usage section.

If there’s a match between a **Booking** and a **usage line** from the **License Server**, the **Booking** is deleted even if the **Grace Time** is not expired yet.
This prevents double booking the license, since **License Manager** would take into account the **Booking** and the usage when updating the total amount of licenses used.

### Reconciliation
For each license tracked by **License Manager**, the **License Manager Agent** will periodically poll the **License Servers** to get
the usage information and store it in the **License Manager API**. This process is called **Reconciliation**. The **stat-interval** is the period of time
between each **Reconciliation** and can be configured in the **License Manager Agent** configuration file.

The **Reconciliation** is also triggered when the **SlurmctldProlog** and **SlurmctldEpilog** run.

The information in the **License Manager API** is used by the **Reconciliation** process to update the license counters in **Slurm**.

#### Slurm License Counters
The license counter in **Slurm** shows the total number of licenses, how many are in use, and how many are reserved.
The counter for licenses-in-use only accounts for licenses being used by jobs running in the cluster and can’t be edited manually.

The licenses can be used anywhere, such as other clusters and desktop applications sharing the same license pool, so the **Reconciliation**
syncs the counters in the cluster with the values in the **License Servers** to account for usage in other environments.

The main issue is that the **Used** counter is a read-only value, which prevents **License Manager** from updating the counter directly.
If this was possible, it would be easier to update the **Used** counter to reflect the actual usage in the **License Server**.
But since it's not possible, **License Manager** uses the **Reservation** to achieve the same result.

#### Slurm Reservation
**Slurm** has the ability to reserve resources to be used by specific users. This can also be used to block resource usage during maintenance downtime, for example.

Due to the **Slurm** counters being immutable, **License Manager Agent** uses this feature to block the licenses that are already in use
in the **License Server**, which can be used in any environment. 

The **Reservation** mechanism should not be confused with the **Booking** created by the **SlurmctldProlog** in the **License Manager API**.

* **Reservation**: Represents the licenses in use in the **License Server** that are not being used by the cluster.
* **Booking**: Represents the licenses that are reserved for a job in the cluster.

To calculate the number of licenses reserved, the following formula is used:

$$
\begin{aligned}
\text{reserved} &= \text{licenses used in License Server} \\
&- \text{licenses used by Slurm} \\
&+ \text{licenses booked}
\end{aligned}
$$

This **Reservation** is not meant to be consumed by users nor jobs; it's only a representation of the licenses in use.

The **Reservation** is created by the user configured in the **License Manager Agent** configuration file. The user must
have a user account in the **Slurm** cluster and have **operator** privilege level to manage **Reservations**.

### License Manager Agent Workflow
Sequence diagram for the timed **Reconciliation**:

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



Sequence diagram for when a job is submitted to *Slurm*:
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

### Configurations
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

### License Servers
The **License Server** resource represents the actual **License Server** where the license is installed.

A **License Server** has a host and a port, and each **Configuration** must have at least one **License Server** related to it.
The **Configuration** can cave multiple **License Servers** for redundancy, as long as they provide the same data.
Each **License Server** will be called, in order, if the previous one is not available.


### Products
The **Product** resource represents the product name of the license.

Each license is identified in the cluster as `product.feature@license_server_type`.
The **Product** is used to group the licenses that are under the same **License Server**

To create a **Feature**, a **Product** needs to be created first.


### Features
The **Feature** resource represents the licenses in the cluster.

Each **Feature** must be related to a **Configuration** and a **Product**.

The **reserved** value represents how many licenses should be reserved for usage in desktop applications. The amount of licenses reserved is not used by the cluster.

**License Manager Agent** polls the **License Server** to populate the **used** and **total** values.
The information stored includes the total number of licenses available, how many licenses are in use in the **License Server** and how many are booked.

The `/lm/features/by_client_id` endpoint extracts the **cluster_client_id** from the request and updates the feature for that cluster. This endpoint is needed since there can be multiple licenses with the same name in different clusters.

The `/lm/features/bulk` endpoint is used by the **License Manager Agent** to update the counters for multiple features with the same request.


### Jobs
The **Job** resource represents the jobs submitted to the cluster.

When a job is submitted to **Slurm**, it is intercepted by the **SlurmctldProlog** script, which creates a **Job** in the **License Manager API**.

Each **Job** can have multiple **Bookings** related to it, depending on the number of licenses requested by the job.

Once the job finishes, the **SlurmctldEpilog** deletes the job from the **License Manager API** , along with its **Bookings**.

Since the  `slurm_job_id` is not unique across clusters, each job is identified by the `cluster_client_id` alongside the `slurm_job_id`.

The endpoint `/lm/jobs/by_client_id` extracts the `cluster_client_id` from the request and returns the jobs that belong to the cluster.

The in the POST endpoint, the parameter `cluster_client_id` is optional. If it's not provided, the `cluster_client_id` is extracted from the request.


### Bookings
The **Booking** resource is responsible for Booking licenses for a specific job.

The **Booking** ensures the job will have enough licenses to be used when it requests them to the **License Server**.

Each **Booking** is related to a **Job**. The `job_id` parameter identifies the **Job** in the **License Manager API**, and is different from the `slurm_job_id`
that idenfies it in the cluster.

### Permissions
The **License Manager API** needs an authentication provider (OIDC) to manage the permissions for the users.

We recommend using the **Keycloak** as the OIDC provider, but any provider that supports the **OIDC** protocol can be used.

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
The **License Manager CLI** is a client to interact with the **License Manager API**.

It can be used to add new configurations to the API and to check the usage information for each tracked license.

The **Jobs** and **Bookings** are read only. The remaining resources can be edited by users with permission to do so.

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
| lm-cli bookings list | List all bookings |
| lm-cli bookings list<br>--search **<search string\>** | Search bookings with the specified string |
| lm-cli bookings list<br>--sort-field **<sort field\>** | Sort bookings by the specified field |
| lm-cli bookings list<br>--sort-field **<sort field\>**<br>--sort-order **<ascending or descending\>**| Sort bookings by the specified order |
