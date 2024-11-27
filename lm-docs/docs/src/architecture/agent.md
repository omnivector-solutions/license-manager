# License Manager Agent
The **License Manager Agent** is the key component that ensures jobs have enough free licenses to execute successfully.
Deployed on the **Slurm** cluster, this agent works in conjunction with the **License Manager API** to track license usage and prevent job failures due to insufficient licenses.  

The agent has two main functionalities:

* Sync the local **Slurm** license counters with the usage from the **License Server**

* Manage the license requests from jobs submitted to the cluster using **Bookings**

Since the **Slurm** license counter doesn't directly interact with **License Servers**, the **License Manager Agent** actively polls the servers for data. Then it updates the corresponding counters in **Slurm**.
Each cluster managed by **License Manager** has a dedicated license counter linked to the **License Server**. This configuration allows for license sharing across multiple clusters.

## Bookings
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

### Deleting Bookings by Grace Time
Depending on the HPC application used by a job, it may take some time to check out the license from the **License Server** after it is submitted to **Slurm**.
It will take longer for jobs that have multiple setup steps before actually starting the application that requires the license.

Thus, each license has a **Grace Time** period that is used to indicate how long a **Booking** will be retained.

After the **Grace Time** expires, the **Booking** is deleted. This means that the license was checked out from the
**License Server** and doesn't need a **Booking** anymore.

If the **Booking** is not deleted once the license is checked out, **License Manager** would account for usage twice: once for the **Booking** and once for the actual usage. This double booking issue is mitigated by the **Grace Time** and by matching the **Booking** with the usage from the **License Server**.

### Deleting Bookings by matching
**License Manager** parses output from each **License Server** to gather information into two main sections:  

* License information: **Used** and **Total** counters

* Usage: how many licenses each **User** is using and the **Lead Host** from where the request was made

The **Booking** from **License Manager** contains the same information as the usage section.

If there’s a match between a **Booking** and a **usage line** from the **License Server**, the **Booking** is deleted even if the **Grace Time** is not expired yet.
This prevents double booking the license, since **License Manager** would take into account the **Booking** and the usage when updating the total amount of licenses used.

## Reconciliation
For each license tracked by **License Manager**, the **License Manager Agent** will periodically poll the **License Servers** to get
the usage information and store it in the **License Manager API**. This process is called **Reconciliation**. The **stat-interval** is the period of time
between each **Reconciliation** and can be configured in the **License Manager Agent** configuration file.

The **Reconciliation** is also triggered when the **SlurmctldProlog** and **SlurmctldEpilog** run.

The information in the **License Manager API** is used by the **Reconciliation** process to update the license counters in **Slurm**.

### Slurm License Counters
The license counter in **Slurm** shows the total number of licenses, how many are in use, and how many are reserved.
The counter for licenses-in-use only accounts for licenses being used by jobs running in the cluster and can’t be edited manually.

The licenses can be used anywhere, such as other clusters and desktop applications sharing the same license pool, so the **Reconciliation**
syncs the counters in the cluster with the values in the **License Servers** to account for usage in other environments.

The main issue is that the **Used** counter is a read-only value, which prevents **License Manager** from updating the counter directly.
If this was possible, it would be easier to update the **Used** counter to reflect the actual usage in the **License Server**.
But since it's not possible, **License Manager** uses the **Reservation** to achieve the same result.

### Slurm Reservation
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

## License Manager Agent Workflow
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

## Reference
The [reference](../reference/agent.md) page contains the parsers, server interfaces, services and backend communication modules available.
