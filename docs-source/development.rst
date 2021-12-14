Development
===========
Development of the `license-manager` is done using a setup that consists of
running a mix of different services in docker and LXD containers.

The general steps to set up a development environment are:

1) a slurm deployment running on LXD with the license-manager-agent
2) a license-manager-simulator deployment running locally)
3) a license-manager backend deployment in docker (deployed using docker-compose)
4) Post deploy modifications
5) Validation

The following text will attempt to describe the process for setting up these systems and perfoming
code changes in the license-manager code base needed to facilitate running a local development environment.

----------------
Pre-Installation
----------------
Before you get started, enusure you have the following pre-requisites installed on your machine.

- snapd
- charmcraft
- LXD (latest/stable)
- juju
- poetry
- docker-compose
- docker

Additionally, assign the host machine's primary ip address to a variable ``MY_IP``. We will use this value throughout the
development environment setup process.

.. code-block:: bash

    MY_IP="$(ip route get 1 | awk '{print $(NF-2);exit}')"

-------------------------------
1) Deploy a local SLURM cluster on LXD
-------------------------------
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

The slurm cluster is now prepared for further configuration and use in ``licnese-manager`` development.

------------------------------------
2) Run the license-manager-simulator 
------------------------------------
To run the license-manager-simulator, clone the repository and run ``make local``.


.. code-block:: bash

   git clone https://github.com/omnivector-solutions/license-manager-simulator
   cd license-manager-simulator/

   make local

---------------------------------
3) Compose the license-manager backend
---------------------------------
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

``docker ps`` shows

.. code-block:: bash

    $ docker ps
    CONTAINER ID   IMAGE                     COMMAND                  CREATED          STATUS                    PORTS                                   NAMES
    a62719b6fa65   backend_license-manager   "uvicorn lm_backend.…"   13 minutes ago   Up 13 minutes             0.0.0.0:7000->80/tcp, :::7000->80/tcp   backend_license-manager_1
    3d5abbc7ffff   postgres                  "docker-entrypoint.s…"   2 days ago       Up 13 minutes (healthy)   5432/tcp                                backend_postgres-back_1

From the output above, we see that port ``7000`` on our local machine is forwarded to the listening port of the license-manager
backend container (port ``80``). This means we will make requests to our local host ip address at port ``7000`` in order to access the
license-manager backend http endpoints.

Now initialize the backend with an example configuration that we can use for testing.

.. code-block:: bash

    curl -X 'POST' \
      'http://$MY_IP:7000/lm/api/v1/config/' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "id": 0,
      "product": "abaqus",
      "features": "{\"abaqus\": 50}",
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
      'http://$MY_IP0:7000/lm/api/v1/config/all' \
      -H 'accept: application/json' | jq

The response should contain the configuration item you created.

.. code-block:: bash

      [
        {
          "id": 0,
          "product": "abaqus",
          "features": {
            "abaqus": 50
          },
          "license_servers": [
            "rats"
          ],
          "license_server_type": "flexlm",
          "grace_time": 30
        }
      ]

The ``license-manager`` backend is now configured and ready for use in the development environment.

--------------------------------------------------
4) Add the license-manager-agent to the cluster
--------------------------------------------------
The final component we need to deploy is the ``license-manager-agent``. The ``license-manager-agent`` is deployed to the
same model as the slurm charms, and related to ``slurmctld``.

.. code-block:: bash

   git clone git@github.com:omnivector-solutions/license-manager-agent
   cd license-manager-agent/

   make charm

Following the ``make charm`` command you should be left with a resultant charm artifact named
``license-manager-agent_ubuntu-20.04-amd64_centos-7-amd64.charm``. This is the charm that we will deploy.

We need to define a configuration file to be used with the license-manager-agent charm.

.. code-block:: bash

   cat <<EOF > license-manager-agent.yaml
   license-manager-agent:
     log-level: DEBUG
     stat-interval: 30
     jwt-key: "your.jwt.key"
     pypi-url: "https://pypicloud.omnivector.solutions"
     pypi-username: "<pypi-username>"
     pypi-password: "<pypi-password>"
     license-manager-backend-base-url: "http://$MY_IP:7000"
     lmstat-path: "/usr/local/bin/lmstat"
     rlmstat-path: "/usr/local/bin/rlmstat"
   EOF

Running the above command will produce a file named ``license-manager-agent.yaml`` with the ip address of your host machine
templated in to the file.

Now that we have the charm artifact (``license-manager-agent_ubuntu-20.04-amd64_centos-7-amd64.charm``) and have generated
the config file for the charm (``license-manager-agent.yaml``), we are ready to deploy.

Using ``juju``, deploy the ``license-manager-agent`` charm to the model, specifying the config file as an argument to the
deploy command..

.. code-block:: bash

   juju deploy ./license-manager-agent_ubuntu-20.04-amd64_centos-7-amd64.charm \
       --config ./license-manager-agent.yaml --series focal

---------------------------
5) Additional Modifications
---------------------------
At this point you should have 3 systems running; 1) slurm cluster in LXD, 2) license-manager-simulator,
3) license-manager backend.

Once the systems have been successfully deployed you will need to apply the post deployment configurations.

To configure the license-manager-simulator we need to add license configurations via the HTTP


-------------
5) Validation
-------------
