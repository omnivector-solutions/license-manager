Development
===========
The ``License Manager`` application incorporates a mix of different services in docker and LXD containers.
This text will attempt to define the procedure for initializing and running the different components.

----------------
Pre-Installation
----------------
Before you get started, ensure you have the following pre-requisites installed on your machine:

- snapd
- charmcraft
- LXD (latest/stable)
- juju
- poetry
- docker-compose
- docker

Additionally, assign the host machine's primary IP address to a variable ``MY_IP``. We will use this value throughout the
development environment setup process.

.. code-block:: bash

    MY_IP="$(ip route get 1 | awk '{print $(NF-2);exit}')"

--------------------------------------
1) Deploy a local SLURM cluster on LXD
--------------------------------------
Follow the `upstream documentation <https://omnivector-solutions.github.io/osd-documentation/master/installation.html#lxd>`_
to deploy a local LXD slurm cluster that we can use in development.

The general idea is to run ``juju deploy slurm``, following which, you will have a local slurm cluster to
use in development.

After the deployment of slurm has completed and settled, the environment should resemble the following:

.. code-block:: bash

   Model                    Controller           Cloud/Region         Version  SLA          Timestamp
   license-manager-testing  localhost-localhost  localhost/localhost  2.9.17   unsupported  06:46:42Z

   App              Version  Status  Scale  Charm            Store     Channel  Rev  OS      Message
   percona-cluster  5.7.20   active      1  percona-cluster  charmhub  stable   302  ubuntu  Unit is ready
   slurmctld        0.8.1    active      1  slurmctld        charmhub  stable    17  ubuntu  slurmctld available
   slurmd           0.8.1    active      1  slurmd           charmhub  stable    26  ubuntu  slurmd available
   slurmdbd         0.8.1    active      1  slurmdbd         charmhub  stable    15  ubuntu  slurmdbd available
   slurmrestd       0.8.1    active      1  slurmrestd       charmhub  stable    15  ubuntu  slurmrestd available

   Unit                Workload  Agent  Machine  Public address  Ports     Message
   percona-cluster/0*  active    idle   0        10.20.96.130    3306/tcp  Unit is ready
   slurmctld/0*        active    idle   1        10.20.96.57               slurmctld available
   slurmd/0*           active    idle   2        10.20.96.233              slurmd available
   slurmdbd/0*         active    idle   3        10.20.96.123              slurmdbd available
   slurmrestd/0*       active    idle   4        10.20.96.62               slurmrestd available

   Machine  State    DNS           Inst id        Series  AZ  Message
   0        started  10.20.96.130  juju-b71748-0  bionic      Running
   1        started  10.20.96.57   juju-b71748-1  focal       Running
   2        started  10.20.96.233  juju-b71748-2  focal       Running
   3        started  10.20.96.123  juju-b71748-3  focal       Running
   4        started  10.20.96.62   juju-b71748-4  focal       Running

Following the deployment, run the action to enlist the `slurmd` node and set it's state to idle.

.. code-block:: bash

   juju run-action slurmd/0 node-configured

Lastly, validate that the node has successfully enlisted and the cluster is operational.

.. code-block:: bash

   $ juju ssh slurmd/0 sinfo
   PARTITION  AVAIL  TIMELIMIT  NODES  STATE NODELIST
   osd-slurmd    up   infinite      1   idle juju-b71748-2

   $ juju ssh slurmd/0 srun -posd-slurmd hostname
   juju-b71748-2

The slurm cluster is now prepared for further configuration and use in ``License Manager`` development.

----------------------------------
2) Compose the License Manager API
----------------------------------
Setting up the ``License Manager API`` for development is done in three steps:

1. Clone the project to your local machine
2. Run ``docker-compose``
3. Initialize the database with a license configuration for testing.

To get started, clone the ``license-manager`` repository from GitHub and run ``make local``.

.. code-block:: bash

    git clone https://github.com/omnivector-solutions/license-manager
    cd license-manager/backend/

    make local

We should now see two running docker containers; ``backend_license-manager_1`` and ``backend_postgres-back_1``.

``docker ps`` shows:

.. code-block:: bash

    $ docker ps
    CONTAINER ID   IMAGE                     COMMAND                  CREATED          STATUS                    PORTS                                   NAMES
    a62719b6fa65   backend_license-manager   "uvicorn lm_backend.…"   13 minutes ago   Up 13 minutes             0.0.0.0:7000->80/tcp, :::7000->80/tcp   backend_license-manager_1
    3d5abbc7ffff   postgres                  "docker-entrypoint.s…"   2 days ago       Up 13 minutes (healthy)   5432/tcp                                backend_postgres-back_1

From the output above, we see that port ``7000`` on our local machine is forwarded to the listening port of the ``License Manager API``
container (port ``80``). This means we will make requests to our local host IP address at port ``7000`` in order to access the ``License Manager API`` HTTP endpoints.

Now initialize the API with the following resources that we can use for testing:

#. Cluster
#. Configuration
#. License server
#. Product
#. Feature

.. code-block:: bash

    CLUSTER_ID=$(curl -X 'POST' \
      'http://'$MY_IP':7000/lm/clusters/' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "name": "OSD Cluster",
      "client_id": "osd-cluster"
      }' | jq '.id')
    
    CONFIG_ID=$(curl -X 'POST' \
      'http://'$MY_IP':7000/lm/configurations/' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "name": "Abaqus",
      "cluster_id": '$CLUSTER_ID',
      "grace_time": 30,
      "type": "flexlm"
      }' | jq '.id')

    curl -X 'POST' \
      'http://'$MY_IP':7000/lm/license_servers/' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "config_id": '$CONFIG_ID',
      "host": "myexampleflexlmhost.example.com",
      "port": 24000
      }'

    PRODUCT_ID=$(curl -X 'POST' \
      'http://'$MY_IP':7000/lm/products/' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "name": "abaqus"
      }' | jq '.id')

    curl -X 'POST' \
      'http://'$MY_IP':7000/lm/features/' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "name": "abaqus",
      "product_id": '$PRODUCT_ID',
      "config_id": '$CONFIG_ID',
      "reserved": 0
      }'

You can check that the resources were successfully added by making a request to list the clusters in the database. (this
list should contain the configuration and license you previously added.)

.. code-block:: bash

    curl -X 'GET' \
      'http://'$MY_IP':7000/lm/clusters' \
      -H 'accept: application/json'

.. code-block:: bash

      [
        {
            "id": 1,
            "name": "OSD Cluster",
            "client_id": "osd-cluster",
            "configurations": [
              {
                "id": 1,
                "name": "Abaqus",
                "cluster_id": 1,
                "features": [
                  {
                    "id": 1,
                    "name": "abaqus",
                    "product": {
                      "id": 1,
                      "name": "abaqus"
                    },
                    "config_id": 1,
                    "reserved": 0,
                    "inventory": {
                      "id": 1,
                      "feature_id": 1,
                      "total": 0,
                      "used": 0
                    }
                  }
                ],
                "license_servers": [
                  {
                    "id": 1,
                    "config_id": 1,
                    "host": "myexampleflexlmhost.example.com",
                    "port": 24000
                  }
                ],
                "grace_time": 30,
                "type": "flexlm"
              }
            ],
            "jobs": []
          }
      ]

The ``License Manager API`` is now configured and ready for use in the development environment.

----------------------------------------
3) Compose the License Manager Simulator
----------------------------------------
To run the ``License Manager Simulator`` API, clone the repository and run ``docker-compose up``.

.. code-block:: bash

   git clone https://github.com/omnivector-solutions/license-manager-simulator
   cd license-manager-simulator/

   docker-compose up

-----------------------------------------------
4) Add the License Manager Agent to the cluster
-----------------------------------------------
The final component we need to deploy is the ``License Manager Agent``. The ``License Manager Agent`` is deployed to the
same model as the slurm charms, and related to ``slurmctld``.

.. code-block:: bash

   git clone git@github.com:omnivector-solutions/charm-license-manager-agent
   cd charm-license-manager-agent/

   make charm

The ``make charm`` command will produce a resultant charm artifact named
``license-manager-agent.charm``. This is the charm that we will deploy.

Before deploying the charm, create a ``yaml`` configuration file that contains the needed settings for the
``License Manager Agent Charm``. The config should look something like this:

.. code-block:: yaml

   license-manager-agent:
     log-level: DEBUG
     stat-interval: 30
     license-manager-backend-base-url: "http://"$MY_IP":7000"
     lmutil-path: "/usr/local/bin/lmutil"
     rlmutil-path: "/usr/local/bin/rlmutil"
     lsdyna-path: "/usr/local/bin/lstc_qrun"
     lmxendutil-path: "/usr/local/bin/lmxendutil"
     olixtool-path: "/usr/local/bin/olixtool"
     oidc-domain: "your-oidc-domain"
     oidc-audience: "your-oidc-audience"
     oidc-client-id: "your-oidc-client-id"
     oidc-client-secret: "your-oidc-client-secret"
     sentry-dsn: ""

Make sure to substitute the correct values into the new ``license-manager-agent.yaml`` configuration file
(especially the IP address of your host machine). You'll also need to provision an OIDC instance to authenticate
against the backend API.

Now that we have the charm artifact (``license-manager-agent.charm``) and
the config file for the charm (``license-manager-agent.yaml``), we are ready to deploy.

Using ``juju``, deploy the ``license-manager-agent`` charm to the model, specifying the config file as an argument to the
deploy command.

.. code-block:: bash

   juju deploy ./license-manager-agent.charm \
       --config ./license-manager-agent.yaml --series focal

After the deploy, make sure to relate the charm to the juju-info and prolog-epilog interface.

.. code-block:: bash

   juju relate license-manager-agent:juju-info slurmctld
   juju relate license-manager-agent:prolog-epilog slurmctld

---------------------------
5) Additional Modifications
---------------------------
At this point you should have 3 systems running:

1. Slurm cluster in LXD
2. License Manager Simulator
3. License Manager Backend

Once the systems have been successfully deployed you will need to apply the post deployment configurations.
These configurations will ensure that your slurm cluster has a fake license server client and available licenses
to be used by the fake application (which will be run as a batch script).

Configuring the license server client
*************************************
The ``License Manager Simulator`` has a script and a template for each license server supported (FlexLM, RLM, LS-Dyna, LM-X and OLicense).
The script requests license information from the ``License Manager Simulator`` API and renders
it in the template, simulating the output from the real license server. These files need to be copied to the ``License Manager Agent`` machine.

You also need to add licenses to the Slurm cluster and to the simulator API. To use the simulated licenses, there's an
application script, which requests a license to the simulator API, sleeps for a few seconds, and return the license. This
application can be submitted as a job using a batch file. These files need to be copied to the slurmd machine.

To set up everything needed to use the simulator, use the make setup command available in the ``License Manager Simulator`` project.
This commands expects as an argument the ``License Manager Simulator`` API IP address.

.. code-block:: bash

   cd license-manager-simulator/
   make setup lm_sim_ip=http://$MY_IP:8000

Using the simulated license servers
***********************************
With the environment configured, you'll have one simulated license for each license server supported:

1. abaqus.abaqus for FlexLM
2. converge.super for RLM
3. mppdyna.mppdyna for LS-Dyna
4. hyperworks.hyperworks for LM-X
5. cosin.ftire_adams for OLicense

These licenses will be available in the simulated license servers. You can check it by executing ``lmutil``, ``rlmutil``, ``lstc_qrun``, ``lmxendutil``
and ``olixtool.lin`` files.

.. code-block:: bash

    juju ssh license-manager-agent/0
    source /srv/license-manager-agent-venv/bin/activate
    /srv/license-manager-agent-venv/lib/python3.8/site-packages/bin/lmutil

The output should display the "abaqus.abaqus" license that was added to the ``License Manager Simulator``:

.. code-block:: bash

    lmutil - Copyright (c) 1989-2012 Flexera Software LLC. All Rights Reserved.
    Flexible License Manager status on Thu 10/29/2020 17:44

    License server status: server1,server2,server3
        License file(s) on server1: f:\flexlm\AbaqusLM\License\license.dat:

    server1: license server UP v11.13
    server2: license server UP (MASTER) v11.13
    server3: license server UP v11.13

    Vendor daemon status (on server2):
      FakeLM: UP v11.13

    Feature usage info:

    Users of abaqus:  (Total of 1000 licenses issued;  Total of 0 licenses in use)

      "abaqus" v62.2, vendor: FakeLM

      floating license

Seeding the batch script and fake application
*********************************************
To test the ``License Manager``, there's a fake application and a batch script. These files are available at the ``/tmp`` folder in the ``slurmd`` machine.
The fake application makes a request to the ``License Manager Simulator`` API to book 42 ``abaqus`` licenses, sleeps for a few seconds, and then deletes the booking after.
The batch script will be responsible for scheduling the fake application job in the slurm cluster.

To run the job, use the ``sbatch`` command.

.. code-block::  bash

    juju ssh slurmd/0 sbatch /tmp/batch.sh

To use other licenses, change the license's name in the ``application.sh`` and ``batch.sh`` file.

-------------
6) Validation
-------------
After following the steps above, you should have a working development environment.
To validate that it is indeed working, submit a job to slurm (using the batch script) and check ``License Manager API``.
Make a request to the ``features`` endpoint.

.. code-block:: bash

    curl -X 'GET' \
      'http://'$MY_IP':7000/lm/features' \
      -H 'accept: application/json'

You should see that the ``used`` value for the license was updated with the value used in the job (42).

.. code-block:: bash

    [
      {
        "id": 1,
        "name": "abaqus",
        "product": {
          "id": 1,
          "name": "abaqus"
        },
        "config_id": 10
        "reserved": 0,
        "inventory": {
          "id": 1,
          "feature_id": 1,
          "total": 1000,
          "used": 42
        }
      }
    ]

You also should have a new job created. To verify this, make a request to the ``jobs`` endpoint.

.. code-block:: bash

    curl -X 'GET' \
      'http://'$MY_IP:7000'/lm/jobs' \
      -H 'accept: application/json'

The job should contain information about the job and also how many licenses were booked by the job.

.. code-block:: bash

    [
      {
        "id": 1,
        "slurm_job_id": "1",
        "cluster_id": 1,
        "username": "ubuntu",
        "lead_host": "juju-d9201d-2",
        "bookings": [
          {
            "id": 1,
            "job_id": 1,
            "feature_id": 1,
            "quantity": 42
          }
        ]
      }
    ]

Wait for a few seconds (for the reconcile to run) and check again. The job and the booking should be deleted
and the ``used`` value will return to its original quantity.
