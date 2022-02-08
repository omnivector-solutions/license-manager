License Manager Architecture
============================
The license-manager is based on a client/backend architecture. The backend consists of a python http API and a
postgresql database. The client consists of a timed reconcile job that runs on the control node in the cluster and
a prolog integration to SLURM.

License Manager Agent
---------------------
The ``lm_agent`` is responsible for keeping the local cluster license totals
in sync with the the 3rd party license server totals and also accounting for
bookings tracked in the backend.

Workload manager support:

* Slurm

License server support:

* FlexLM
* RLM


Reconcile
*********
The reconcile timed job collects license usage from the 3rd party license servers
and updates the license-manager backend on a periodic basis referred to as the ``stat-interval``.

Workload Manager Bindings
*************************
When Slurm is configured to use the ``PrologSlurmctld`` provided by ``lm_agent``, it will make a
request to the license-manager backend to book the needed licenses prior to the allocation of a job.
The ``PrologSlurmctld`` will exit with status ``1`` if the booking cannot be made and ``0`` if the booking succeeds.

License Manager Backend
-----------------------
The license-manager backend provides an http interface to a postgresql database where
licenses, bookings and license configurations are tracked.

Backend base API routes:

* ``/license``
* ``/booking``
* ``/config``
