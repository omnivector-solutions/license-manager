License Manager Architecture
============================
The License Manager is based on a client/backend architecture. The backend consists of a RESTful API built with Python over a
PostgreSQL database. The client consists of a timed reconcile job that runs on the control node in the cluster and
a prolog integration to Slurm.

License Manager Agent
---------------------
The ``License Manager Agent`` is responsible for keeping the local cluster license totals
in sync with the the 3rd party license server totals. It's also responsible for making booking requests
to the ``License Manager API`` when Slurm is configured to use the ``PrologSlurmctld`` script provided by ``License Manager Agent``.

Reconciliation
**************
For each license tracked by License Manager, the ``License Manager Agent`` will periodically poll the license servers to get
the usage information and store it in the ``License Manager API``. The ``stat-interval`` is the period of time
between each reconciliation and can be configured in the ``License Manager Agent`` configuration file.

The information in the ``License Manager API`` is used by the reconciliation process to update the license counters in Slurm.
This is done by creating a reservation to represent the licenses used in the license server.

This reservation is not meant to be consumed by users nor jobs; it's only a representation of the licenses in use.
The reservation is created by the user configured in the ``License Manager Agent`` configuration file. The user must
have a user account in the Slurm cluster and have ``operator`` privilege level to manage reservations.

Bookings
********
The ``License Manager Agent`` is also responsible for making booking requests to the ``License Manager API``
when Slurm is configured to use the ``PrologSlurmctld`` script provided by ``License Manager Agent``.

Each job submitted to Slurm will trigger the ``PrologSlurmctld`` script that makes a request to the ``License Manager API``
to book the needed licenses prior to the allocation of the job. The booking ensures that the licenses are available for the job
to use by taking into consideration the licenses booked for other jobs and the license usage in the license server.

If the booking cannot be made, the job will be kept in the queue until there are enough licenses available to
satisfy the booking request.

Grace time
**********
A job can take some time to check out the license from the license server after it is submitted to Slurm.
Thus, each license has a ``grace time`` period that is used to indicate how long a booking will be retained.
After the ``grace time`` expires, the booking is deleted. This means that the license was checked out from the
license server and doesn't need a booking anymore.

License Manager API
-------------------
The ``License Manager API`` provides a RESTful API where licenses and bookins are tracked.
The ``License Manager Agent`` uses this API to store the license usage information and to process the booking requests.
The ``License Manager CLI`` interacts with this API to add new configurations and to check the usage information for each tracked license.

The API is also responsible for verifying if the booking requests can be satisfied by accounting for bookings already
made and the license usage in the license server.

The API contains 8 entities that have relationship among them.
This means that some of the resources need to be created before others can be created as well.

.. mermaid::

    erDiagram
        Bookings {
            int id pk
            int job_id pk
            int feature_id pk
            int quantity
        }
        Features {
            int id pk,fk
            int config_id pk
            int product_id pk
            str name 
        }
        Inventories {
            int id pk
            int feature_id fk
            int total
            int used
        }
        Products {
            int id pk
            str name
        }
        Jobs {
            int id pk, fk
            str slurm_job_id
            str cluster_id fk
            str username
            str lead_host
        }
        Clusters {
            int id pk
            str name
            str client_id
        }
        Configurations {
            int id pk
            str name
            int cluster_id fk
            int grace_time
            int reserved
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
        Clusters ||--o{ Jobs : ""
        Products ||--o{ Features : ""
        Features ||--|| Inventories : ""
        Configurations ||--|{ Features : ""
        Clusters ||--o{ Configurations : ""
        Configurations ||--|{ LicenseServers : ""
        
Clusters
********
The ``Cluster`` resource represents the cluster where ``License Manager Agent`` is running.

It must have a ``client_id`` that identifies it in the OIDC provider.

Endpoints available:

* POST ``/lm/clusters``
* GET ``/lm/clusters``
* GET ``/lm/clusters/{id}``
* PUT ``/lm/clusters/{id}``
* DEL ``/lm/clusters/{id}``

Payload example for POST:

.. code-block:: json

    {
        "name": "cluster-name",
        "client_id": "cluster-client-id"
    }

Configurations
**************
The ``Configuration`` resource holds the information for a set of features that are available on the same license server.

A configuration is attached to a cluster and can have ``n`` features attached to it.
It also defines the license type, the license server host addresses and the grace time period.
The license type identifies the provider of the license server.


The following license server types are supported:

* FlexLM
* RLM
* LS-Dyna
* LM-X
* OLicense

Endpoints available:

* POST ``/lm/configurations``
* GET ``/lm/configurations``
* GET ``/lm/configurations/{id}``
* PUT ``/lm/configurations/{id}``
* DEL ``/lm/configurations/{id}``

Payload example for POST:

.. code-block:: json

    {
        "name": "configuration-name",
        "cluster_id": 1, 
        "grace_time": 60,
        "type": "flexlm"
    }

After creating a configuration, the license servers and features can be added.

License Servers
***************
The ``License Server`` resource represents the actual license server where the license is installed.

A license server has a host and a port, and needs to be attached to a configuration.
Each configuration can have ``n`` license servers, as long as they provide the same data (mirrored for redundancy).

Endpoints available:

* POST ``/lm/license_servers``
* GET ``/lm/license_servers``
* GET ``/lm/license_servers/{id}``
* PUT ``/lm/license_servers/{id}``
* DEL ``/lm/license_servers/{id}``

Payload example for POST:

.. code-block:: json

    {
        "config_id": 1,
        "host": "licserv0001",
        "port": 1234
    }


Products
********
The ``Product`` resource represents the product name of the license.

Each license is identified as ``product.feature@license_server_type``.
To create a ``Feature``, a ``Product`` needs to be created first.

Endpoints available:

* POST ``/lm/products``
* GET ``/lm/products``
* GET ``/lm/products/{id}``
* PUT ``/lm/products/{id}``
* DEL ``/lm/products/{id}``

Payload example for POST:

.. code-block:: json

    {
        "name": "abaqus"
    }


Features
********
The ``Feature`` resource represents the licenses in the cluster.

Each ``Feature`` is attached to a ``Configuration`` and a ``Product``.

The feature has a ``reserved`` value, that represents how many licenses should be reserved for usage in desktop applications.
The amount of licenses reserved is not used by the cluster.

Each ``Feature`` has one ``Inventory`` attached to it, which is automatically created when a ``Feature`` is created.
The ``License Manager Agent`` polls the license server to populate the ``Inventory``.
The information stored includes the total number of licenses available and how many licenses are in use.

Endpoints available:

* POST ``/lm/features``
* GET ``/lm/features``
* GET ``/lm/features/{id}``
* PUT ``/lm/features/{id}``
* PUT ``/lm/features/{id}/update_inventory``
* DEL ``/lm/features/{id}``

Payload example for POST:

.. code-block:: json

    {
        "name": "abaqus",
        "product_id": 1,
        "config_id": 1,
        "reserved": 50,
    }

Payload example for PUT ``update_inventory``:

.. code-block:: json

    {
        "total": 500,
        "used": 150
    }

Jobs
****
The ``Job`` resource represents the jobs submitted to the cluster.

When a job is intercepted by the ``PrologSlurmctld`` script, the job is created automatically.

Each ``Job`` can have ``n`` ``Bookings`` attached to it.
If the job requires licenses, a ``Booking`` is created for each license.
Once the job finishes, the ``EpilogSlurmctld`` deletes the job from the API, along with its bookings.

Since the ``slurm_job_id`` is not unique across clusters, each job is identified by the ``cluster_id`` alongside the ``slurm_job_id``.

Endpoints available:

* POST ``/lm/jobs``
* GET ``/lm/jobs``
* GET ``/lm/jobs/{id}``
* DEL ``/lm/jobs/{id}``
* GET ``/lm/jobs/slurm_job_id/{slurm_job_id}/cluster/{cluster_id}``
* DEL ``/lm/jobs/slurm_job_id/{slurm_job_id}/cluster/{cluster_id}``

Payload example for POST:

.. code-block:: json

    {
        "slurm_job_id": "123",
        "cluster_id": 1,
        "username": "user123",
        "lead_host": "host1"
    }

Bookings
********
The ``Booking`` resource is responsible for booking licenses for a specific job.

The booking ensures the job will have enough licenses to be used when the ``grace time`` is reached.
``License Manager Agent`` stores the information about the booking requests made by Slurm when the ``PrologSlurmctld``
script is used.

Each ``Booking`` is attached to a ``Job``. The ``job_id`` parameter identifies the job in the API, and is different from the ``slurm_job_id``
that idenfies it in the cluster.

Endpoints available:

* POST ``/lm/bookings``
* GET ``/lm/bookings``
* GET ``/lm/bookings/{id}``
* DEL ``/lm/bookings/{id}``

Payload example for POST:

.. code-block:: json

    {
        "job_id": 1
        "feature_id": 1,
        "quantity": 50
    }

License Manager CLI
---------------------
The ``License Manager CLI`` is a client to interact with the ``License Manager API``.

It can be used to add new configurations to the API and to check the usage information for each tracked license.

The ``Jobs``, ``Bookings`` and ``Inventories`` are read only. The remaining resources can be edited by users with permission to do so.

Global commands
***************
+-----------------------------------------------------------------------------+----------------------------------------------------+
| **Command**                                                                 | **Description**                                    |   
+=============================================================================+====================================================+
| lm-cli login                                                                | Generate a URL for logging in via browser          |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli show-token                                                           | Print your access token (created after logging in) |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli logout                                                               | Logout and remove your access token                |
+-----------------------------------------------------------------------------+----------------------------------------------------+

Cluster commands
****************
+-----------------------------------------------------------------------------+----------------------------------------------------+
| **Command**                                                                 | **Description**                                    |   
+=============================================================================+====================================================+
| lm-cli clusters list                                                        | List all clusters                                  |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli clusters list                                                        | Search clusters with the specified string          |
|                                                                             |                                                    |
| --search <search string>                                                    |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli clusters list                                                        | Sort clusters by the specified field               |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli clusters list                                                        | Sort clusters by the specified order               |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
|                                                                             |                                                    |
| --sort-order ascending                                                      |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli clusters get-one                                                     | List the cluster with the specified id             |
|                                                                             |                                                    |
| --id <cluster id>                                                           |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli clusters create                                                      | Create a new cluster                               |
|                                                                             |                                                    |
| --name <cluster name>                                                       |                                                    |
|                                                                             |                                                    |
| --client-id <cluster identification in the OIDC provider>                   |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli clusters delete                                                      | Delete the cluster with the specified id           |
|                                                                             |                                                    |
| --id <id to delete>                                                         |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+

Configuration commands
**********************
+-----------------------------------------------------------------------------+----------------------------------------------------+
| **Command**                                                                 | **Description**                                    |   
+=============================================================================+====================================================+
| lm-cli configurations list                                                  | List all configurations                            |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli configurations list                                                  | Search configurations with the specified string    |
|                                                                             |                                                    |
| --search <search string>                                                    |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli configurations list                                                  | Sort configurations by the specified field         |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli configurations list                                                  | Sort configurations by the specified order         |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
|                                                                             |                                                    |
| --sort-order ascending                                                      |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli configurations get-one                                               | List the configuration with the specified id       |
|                                                                             |                                                    |
| --id <configuration id>                                                     |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli configurations create                                                | Create a new configuration                         |
|                                                                             |                                                    |
| --name <configuration name>                                                 |                                                    |
|                                                                             |                                                    |
| --cluster-id <id of the cluster where the configuration applies             |                                                    |
|                                                                             |                                                    |
| --grace-time <grace time in seconds>                                        |                                                    |
|                                                                             |                                                    |
| --license-server-type <license server type>                                 |                                                    |
|                                                                             |                                                    |
| --client-id <cluster identification where the license is configured>        |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli configurations delete                                                | Delete the configuration with the specified id     |
|                                                                             |                                                    |
| --id <id to delete>                                                         |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+

License server commands
***********************
+-----------------------------------------------------------------------------+----------------------------------------------------+
| **Command**                                                                 | **Description**                                    |   
+=============================================================================+====================================================+
| lm-cli license-servers list                                                 | List all license servers                           |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli license-servers list                                                 | Search license servers with the specified string   |
|                                                                             |                                                    |
| --search <search string>                                                    |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli license-servers list                                                 | Sort license servers by the specified field        |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli license-servers list                                                 | Sort license servers by the specified order        |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
|                                                                             |                                                    |
| --sort-order ascending                                                      |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli license-servers get-one                                              | List the license server with the specified id      |
|                                                                             |                                                    |
| --id <license server id>                                                    |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli license-servers create                                               | Create a new license server                        |
|                                                                             |                                                    |
| --config-id <id of the configuration to add the license server>             |                                                    |
|                                                                             |                                                    |
| --host <hostname of the license server>                                     |                                                    |
|                                                                             |                                                    |
| --port <port of the license server>                                         |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli license-servers delete --id <id to delete>                           | Delete the license server with the specified id    |
|                                                                             |                                                    |
| --id <id to delete>                                                         |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+

Product commands
****************
+-----------------------------------------------------------------------------+----------------------------------------------------+
| **Command**                                                                 | **Description**                                    |   
+=============================================================================+====================================================+
| lm-cli products list                                                        | List all products                                  |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli products list                                                        | Search products with the specified string          |
|                                                                             |                                                    |
| --search <search string>                                                    |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli products list                                                        | Sort products by the specified field               |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli products list                                                        | Sort products by the specified order               |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
|                                                                             |                                                    |
| --sort-order ascending                                                      |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli products get-one                                                     | List the product with the specified id             |
|                                                                             |                                                    |
| --id <product id>                                                           |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli products create                                                      | Create a new product                               |
|                                                                             |                                                    |
| --name <product name>                                                       |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli products delete                                                      | Delete the product with the specified id           |
|                                                                             |                                                    |
| --id <id to delete>                                                         |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+

Feature commands
****************
+-----------------------------------------------------------------------------+----------------------------------------------------+
| **Command**                                                                 | **Description**                                    |   
+=============================================================================+====================================================+
| lm-cli features list                                                        | List all features                                  |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli features list                                                        | Search features with the specified string          |
|                                                                             |                                                    |
| --search <search string>                                                    |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli features list                                                        | Sort features by the specified field               |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli features list                                                        | Sort features by the specified order               |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
|                                                                             |                                                    |
| --sort-order ascending                                                      |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli features get-one                                                     | List the feature with the specified id             |
|                                                                             |                                                    |
| --id <feature id>                                                           |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli features create                                                      | Create a new feature                               |
|                                                                             |                                                    |
| --name <feature name>                                                       |                                                    |
|                                                                             |                                                    |
| --product-id <id of the product of the license>                             |                                                    |
|                                                                             |                                                    |
| --config-id <id of the configuration of the license>                        |                                                    |
|                                                                             |                                                    |
| --reserved <how many licenses should be reserved for desktop enviroments>   |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli features delete                                                      | Delete the feature with the specified id           |
|                                                                             |                                                    |
| --id <id to delete>                                                         |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+

Job commands
************
+-----------------------------------------------------------------------------+----------------------------------------------------+
| **Command**                                                                 | **Description**                                    |   
+=============================================================================+====================================================+
| lm-cli jobs list                                                            | List all jobs                                      |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli jobs list                                                            | Search jobs with the specified string              |
|                                                                             |                                                    |
| --search <search string>                                                    |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli jobs list                                                            | Sort jobs by the specified field                   |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli jobs list                                                            | Sort jobs by the specified order                   |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
|                                                                             |                                                    |
| --sort-order ascending                                                      |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+

Booking commands
****************
+-----------------------------------------------------------------------------+----------------------------------------------------+
| **Command**                                                                 | **Description**                                    |   
+=============================================================================+====================================================+
| lm-cli bookings list                                                        | List all bookings                                  |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli bookings list                                                        | Search bookings with the specified string          |
|                                                                             |                                                    |
| --search <search string>                                                    |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli bookings list                                                        | Sort bookings by the specified field               |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+
| lm-cli bookings list                                                        | Sort bookings by the specified order               |
|                                                                             |                                                    |
| --sort-field <sort field>                                                   |                                                    |
|                                                                             |                                                    |
| --sort-order ascending                                                      |                                                    |
+-----------------------------------------------------------------------------+----------------------------------------------------+