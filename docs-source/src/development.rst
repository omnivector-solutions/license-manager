Development
===========
The ``license-manager`` application incorporates a mix of different services in docker and LXD containers.
This text will attempt to define the procedure for initializing and running the different components.

----------------
Pre-Installation
----------------
Before you get started, enusure you have the following pre-requisites installed on your machine:

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

The slurm cluster is now prepared for further configuration and use in ``license-manager`` development.

------------------------------------
2) Run the license-manager-simulator
------------------------------------
To run the license-manager-simulator, clone the repository and run ``make local``.


.. code-block:: bash

   git clone https://github.com/omnivector-solutions/license-manager-simulator
   cd license-manager-simulator/

   make local

At this point you will need to create the artificial license in the license-manager-simulator
backend.

.. code-block:: bash

   curl -X 'POST' \
      'http://$MY_IP:8000/licenses/' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "name": "product.feature"
      "total": 5000
    }'

You should receive a 201 response.

.. code-block:: bash

   {
     "name": "product.feature",
     "total": 5000,
     "id": 2,
     "licenses_in_use": [],
     "in_use": 0
   }

The ``license-manager-simulator`` is now configured for use with the rest of the system.


--------------------------------------
3) Compose the license-manager backend
--------------------------------------
Setting up the license-manager backend for development is done in three steps:

1. Clone the project to your local machine
2. Run ``docker-compose``
3. Initialize the database with a license configuration for testing.

To get started, clone the license-manager repository from github and run ``docker-compose up``.

.. code-block:: bash

    git clone https://github.com/omnivector-solutions/license-manager
    cd license-manager/backend/

    docker-compose up

We should now see two running docker containers; ``backend_license-manager_1`` and ``backend_postgres-back_1``.

``docker ps`` shows:

.. code-block:: bash

    $ docker ps
    CONTAINER ID   IMAGE                     COMMAND                  CREATED          STATUS                    PORTS                                   NAMES
    a62719b6fa65   backend_license-manager   "uvicorn lm_backend.…"   13 minutes ago   Up 13 minutes             0.0.0.0:7000->80/tcp, :::7000->80/tcp   backend_license-manager_1
    3d5abbc7ffff   postgres                  "docker-entrypoint.s…"   2 days ago       Up 13 minutes (healthy)   5432/tcp                                backend_postgres-back_1

From the output above, we see that port ``7000`` on our local machine is forwarded to the listening port of the license-manager
backend container (port ``80``). This means we will make requests to our local host IP address at port ``7000`` in order to access the
license-manager backend http endpoints.

Now initialize the backend with an example configuration that we can use for testing.

.. code-block:: bash

    curl -X 'POST' \
      'http://$MY_IP:7000/lm/api/v1/config/' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "id": 0,
      "product": "product",
      "features": "{\"feature\": 50}",
      "license_servers": [
        "flexlm:myexampleflexlmhost.example.com:24000"
      ],
      "license_server_type": "flexlm",
      "grace_time": 30
    }'

You can check that the configuration was successfully added by making a request to list the configurations in the database. (this
list should contain the configuration you previously added.)

.. code-block:: bash

    curl -X 'GET' \
      'http://$MY_IP:7000/lm/api/v1/config/all' \
      -H 'accept: application/json'

The 201 HTTP response should contain the configuration item you created.

.. code-block:: bash

      [
        {
          "id": 0,
          "product": "product",
          "features": {
            "feature": 50
          },
          "license_servers": [
            "flexlm:myexampleflexlmhost.example.com:24000"
          ],
          "license_server_type": "flexlm",
          "grace_time": 30
        }
      ]

The ``license-manager`` backend is now configured and ready for use in the development environment.

-----------------------------------------------
4) Add the license-manager-agent to the cluster
-----------------------------------------------
The final component we need to deploy is the ``license-manager-agent``. The ``license-manager-agent`` is deployed to the
same model as the slurm charms, and related to ``slurmctld``.

.. code-block:: bash

   git clone git@github.com:omnivector-solutions/license-manager-agent
   cd license-manager-agent/

   make charm

The ``make charm`` command will produce a resultant charm artifact named
``license-manager-agent_ubuntu-20.04-amd64_centos-7-amd64.charm``. This is the charm that we will deploy.

Before deploying the charm, create a ``yaml`` configuration file that contains the needed settings for the
license-manager-agent charm. The config should look something like this:

.. code-block:: yaml

   license-manager-agent:
     log-level: DEBUG
     stat-interval: 30
     jwt-key: "your.jwt.key"
     pypi-url: "https://pypicloud.omnivector.solutions"
     pypi-username: "<pypi-username>"
     pypi-password: "<pypi-password>"
     license-manager-backend-base-url: "http://$MY_IP:7000"
     lmutil-path: "/usr/local/bin/lmutil"
     rlmutil-path: "/usr/local/bin/rlmutil"
     lsdyna-path: "/usr/local/bin/lstc_qrun"
     lmxendutil-path: "/usr/local/bin/lmxendutil"
     sentry-dsn: ""

Make sure to substitute the correct values into the new ``license-manager-agent.yaml`` configuration file
(especially the IP address of your host machine)

Now that we have the charm artifact (``license-manager-agent_ubuntu-20.04-amd64_centos-7-amd64.charm``) and
the config file for the charm (``license-manager-agent.yaml``), we are ready to deploy.

Using ``juju``, deploy the ``license-manager-agent`` charm to the model, specifying the config file as an argument to the
deploy command.

.. code-block:: bash

   juju deploy ./license-manager-agent_ubuntu-20.04-amd64_centos-7-amd64.charm \
       --config ./license-manager-agent.yaml --series focal

After the deploy, make sure to relate the charm to the juju-info and prolog-epilog interface.

.. code-block:: bash

   juju relate license-manager-agent:juju-info slurmctld
   juju relate license-manager-agent:prolog-epilog slurmctld

---------------------------
5) Additional Modifications
---------------------------
At this point you should have 3 systems running:

1. slurm cluster in LXD
2. license-manager-simulator
3. license-manager backend

Once the systems have been successfully deployed you will need to apply the post deployment configurations.
These configurations will ensure that your slurm cluster has a fake license server client and available licenses
to be used by the fake application (which will be run as a batch script).

Configuring the slurm cluster in LXD
************************************
Before being able to run jobs, the slurm cluster must have a partition and licenses added to it.
Use the ``juju config`` command to create a partition.

.. code-block:: bash

    juju config slurmd partition-name=mypartition

Add the license to the cluster using the ``sacctmgr`` command.

.. code-block:: bash

    juju ssh slurmctld/0 sudo sacctmgr add resource Type=license Clusters=osd-cluster \
        Server=flexlm Names=product.feature Count=50 ServerType=flexlm  PercentAllowed=100 -i

Configuring the fake license server client
******************************************
Modify the fake license server files available in the license-manager-simulador ``bin`` folder.
The modifications that must be made in ``lms-util.py``, ``rlm-util.py``, ``lsdyna-util.py`` and ``lmx-util.py`` files are:

1. change shebang to "#!/srv/license-manager-agent-venv/bin/python3.8";
2. change template path to "/srv/license-manager-agent-venv/bin/python3.8/site-packages/bin";
3. change the URL to the IP address of where the ``license-manager-simulator`` is running;

Copy the modified files and the templates to the cluster machine where the license manager agent is running.

.. code-block:: bash

    juju scp bin/flexlm.out.tmpl license-manager-agent/0:/tmp
    juju scp bin/rlm.out.tmpl license-manager-agent/0:/tmp
    juju scp bin/lsdyna.out.tmpl license-manager-agent/0:/tmp
    juju scp bin/lmx.out.tmpl license-manager-agent/0:/tmp
    
    juju scp bin/lms-util.py license-manager-agent/0:/tmp
    juju scp bin/rlm-util.py license-manager-agent/0:/tmp
    juju scp bin/lsdyna-util.py license-manager-agent/0:/tmp
    juju scp bin/lmx-util.py license-manager-agent/0:/tmp

With the files in the ``/tmp`` folder, ssh into the machine to rename, set the permission and move them to the correct location.

.. code-block:: bash

    juju ssh license-manager-agent/0

    cd /tmp

    sudo mv lms-util.py lmutil
    sudo mv rlm-util.py rlmutil
    sudo mv lsdyna-util.py lstc_qrun
    sudo mv lmx-util.py lmxendutil

    sudo chmod +x lmutil
    sudo chmod +x rlmutil
    sudo chmod +x lstc_qrun
    sudo chmod +x lmxendutil

    sudo mv lmutil /srv/license-manager-agent-venv/lib/python3.8/site-packages/bin
    sudo mv rlmutil /srv/license-manager-agent-venv/lib/python3.8/site-packages/bin
    sudo mv lstc_qrun /srv/license-manager-agent-venv/lib/python3.8/site-packages/bin
    sudo mv lmxenditul /srv/license-manager-agent-venv/lib/python3.8/site-packages/bin

    sudo mv flexlm.out.tmpl /srv/license-manager-agent-venv/lib/python3.8/site-packages/bin
    sudo mv rlm.out.tmpl /srv/license-manager-agent-venv/lib/python3.8/site-packages/bin
    sudo mv lsdyna.out.tmpl /srv/license-manager-agent-venv/lib/python3.8/site-packages/bin
    sudo mv lmx.out.tmpl /srv/license-manager-agent-venv/lib/python3.8/site-packages/bin

To be able to render the templates, activate the virtual enviroment in the license manager agent machine and install ``jinja2``.

.. code-block:: bash

    juju ssh license-manager-agent/0
    source /srv/license-manager-agent-venv/bin/activate
    pip install jinja2

Now you must be able to simulate FlexLM, RLM, LS-Dyna and LM-X license servers. You can check it by executing ``lmutil``, ``rlmutil``, ``lstc_qrun`` and ``lmxendutil`` files.

.. code-block:: bash

    juju ssh license-manager-agent/0
    source /srv/license-manager-agent-venv/bin/activate
    /srv/license-manager-agent-venv/lib/python3.8/site-packages/bin/lmutil

The output should display the "product.feature" license that was added to the license manager simulator:

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

    Users of product.feature:  (Total of 5000 licenses issued;  Total of 0 licenses in use)

      "product.feature" v62.2, vendor: FakeLM

      floating license

Configuring the license manager agent charm
*******************************************
The license manager agent charm is responsible for downloading the correct agent package from ``pypi``.
There's a juju action to specify which version of the package you want.

.. code-block:: bash

    juju run-action license-manager-agent/0 upgrade-to-latest version=2.1.0 --wait

You should also make sure you have used the correct configurations for the agent. Some of them were already specified in the ``license-manager-agent.yaml``
file. In case you need to update them, use the ``juju config`` command.

.. code-block:: bash

    juju config license-manager-agent sentry-dsn=""
    juju config license-manager-agent lmutil-path=/srv/license-manager-agent-venv/lib/python3.8/site-packages/bin/lmutil
    juju config license-manager-agent rlmutil-path=/srv/license-manager-agent-venv/lib/python3.8/site-packages/bin/rlmutil
    juju config license-manager-agent lsdyna-path=/srv/license-manager-agent-venv/lib/python3.8/site-packages/bin/lstc_qrun
    juju config license-manager-agent lmx-path=/srv/license-manager-agent-venv/lib/python3.8/site-packages/bin/lmxendutil

Lasty, restart the license manager agent service and timer.

.. code-block:: bash

    juju ssh license-manager-agent/0 sudo systemctl daemon-reload
    juju ssh license-manager-agent/0 sudo systemctl start license-manager-agent.timer
    juju ssh license-manager-agent/0 sudo systemctl start license-manager-agent.service


Seeding the batch script and fake application
*********************************************
To test the license manager, there's a fake application and a batch script to run it inside the license-manager-simulator ``job`` folder.
The fake application makes a request to the license-manager-simulator API to book 42 licenses, sleeps for a few seconds, and then deletes the booking after.
The batch script will be responsible for scheduling the fake application job in the slurm cluster.

Copy the files to the slurmd machine ``/tmp`` folder. Also modify the URL in the ``application.sh`` to reflect the IP address of the machine where the
license-manager-simulator is running. The ``license_name`` field in the payload must match the license added to the simulator ("product.feature").

.. code-block:: bash

    juju scp /job/application.sh slurmd/0:/tmp
    juju scp /job/batch.sh slurmd/0:/tmp

To run the job, use the ``sbatch`` command.

.. code-block::  bash

    juju ssh slurmd/0 sbatch /tmp/batch.sh

-------------
5) Validation
-------------
After following the steps above, you should have a working development environment.
To validate that it is indeed working, submit a job to slurm (using the batch script) and check license manager backend.
Make a request to the ``license`` endpoint.

.. code-block:: bash

    curl -X 'GET' \
      'http://$MY_IP:7000/lm/api/v1/license/all' \
      -H 'accept: application/json'

You should see that the ``used`` value for the license was updated with the value used in the job (42).

.. code-block:: bash

    [
      {
        "product_feature": "product.feature",
        "used": 42,
        "total": 50,
        "available": 8
      }
    ]

You also should have a new booking created. To verify this, make a request to the ``booking`` endpoint.

.. code-block:: bash

    curl -X 'GET' \
      'http://$MY_IP:7000/lm/api/v1/booking/all' \
      -H 'accept: application/json'

The booking should contain information about the job and the cluster, and also how many licenses were booked by the job.

.. code-block:: bash

    [
      {
        "id": 1,
        "job_id": "1",
        "product_feature": "product.feature",
        "booked": 42,
        "config_id": 1,
        "lead_host": "juju-d9201d-2",
        "user_name": "ubuntu",
        "cluster_name": "osd-cluster"
      }
    ]



Wait for a few seconds (for the reconcile to run) and check again. The booking should be deleted
and the ``used`` value will return to its original quantity.
