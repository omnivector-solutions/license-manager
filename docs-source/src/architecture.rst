License Manager Architecture
============================
The License Manager is based on a client/backend architecture. The backend consists of a RESTful API built with Python over a
PostgreSQL database. The client consists of a timed reconcile job that runs on the control node in the cluster and
a prolog integration to Slurm.

License Manager Agent
---------------------
The ``license-manager-agent`` is responsible for keeping the local cluster license totals
in sync with the the 3rd party license server totals. It's also responsible for making booking requests
to the ``license-manager-backend`` when Slurm is configured to use the ``PrologSlurmctld`` script provided by ``license-manager-agent``.

Reconciliation
**************
For each license tracked by License Manager, the ``license-manager-agent`` will periodically poll the license server to get
the usage information and store it in the ``license-manager-backend``. The ``stat-interval`` is the period of time
between each reconciliation and can be configured in the ``license-manager-agent`` configuration file.

The information in the ``license-manager-backend`` is used by the reconciliation process to update the license counters in Slurm.
This is done by creating a reservation to represent the licenses used in the license server.

This reservation is not meant to be consumed by users nor jobs; it's only a representation of the licenses in use.
The reservation is created by the user configured in the ``license-manager-agent`` configuration file. The user must
have a user account in the Slurm cluster and have ``operator`` privilege level to manage reservations.

Bookings
********
The ``license-manager-agent`` is also responsible for making booking requests to the ``license-manager-backend``
when Slurm is configured to use the ``PrologSlurmctld`` script provided by ``license-manager-agent``.

Each job submitted to Slurm will make a request to the ``license-manager-backend`` to book the needed licenses prior
to the allocation of the job. The booking ensures that the licenses are available for the job to use by taking into
consideration the licenses booked for other jobs and the license usage in the license server.

If the booking cannot be made, the job will be kept in the queue until there are enough licenses available to
satisfy the booking request.

Grace time
**********
A job can take some time to check out the license from the license server after it is submitted to Slurm.
Thus, each license has a ``grace time`` period that is used to indicate how long a booking will be retained.
After the ``grace time`` expires, the booking is deleted. This means that the license was checked out from the
license server and doesn't need a booking anymore.

License Manager Backend
-----------------------
The ``license-manager-backend`` provides a RESTful API where licenses, bookings and license configurations are tracked.
The ``license-manager-agent`` uses this API to store the license usage information and to process the booking requests.

The backend is also responsible for verifying if the booking requests can be satisfied by accounting for bookings already
made and the license usage in the license server.

Configurations
**************
Each license tracked by License Manager has a configuration that defines the license type, the license server host
addresses and the grace time period. The license type identifies the provider of the license server.

The following license server are supported:

* FlexLM
* RLM
* LS-Dyna
* LM-X
* OLicense

Licenses
********
The ``license-manager-agent`` stores the information polled from the license server for each license configured.
The information stored includes the total number of licenses available, how many licenses are in use and which user checked out the license.

Bookings
********
The ``license-manager-agent`` stores the information about the booking requests made by Slurm when the ``PrologSlurmctld``
script is used. The information stored includes the job id, the user that made the booking request and the number of licenses being booked.
