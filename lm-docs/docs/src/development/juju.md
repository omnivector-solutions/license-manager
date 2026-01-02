# Setting up License Manager using Juju

## Pre-Installation
Before you get started, ensure you have the following pre-requisites installed on your machine:

* snapd
* charmcraft
* LXD (latest/stable)
* juju
* uv
* docker compose
* docker

Additionally, assign the host machine's primary IP address to a variable `MY_IP`. We will use this value throughout the
development environment setup process.

``` bash
MY_IP="$(ip route get 1 | awk '{print $(NF-2);exit}')"
```

## 1. Deploy a local SLURM cluster on LXD
Follow the [upstream documentation](https://omnivector-solutions.github.io/osd-documentation/master/installation.html#lxd)
to deploy a local LXD slurm cluster that we can use in development.

The general idea is to run `juju deploy slurm`, following which, you will have a local slurm cluster to
use in development.

After the deployment of slurm has completed and settled, the environment should resemble the following:

``` bash
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
```

Following the deployment, run the action to enlist the `slurmd` node and set its state to idle.

``` bash
juju run-action slurmd/0 node-configured
```

Lastly, validate that the node has successfully enlisted and the cluster is operational.

``` bash
$ juju ssh slurmd/0 sinfo
PARTITION  AVAIL  TIMELIMIT  NODES  STATE NODELIST
osd-slurmd    up   infinite      1   idle juju-b71748-2

$ juju ssh slurmd/0 srun -posd-slurmd hostname
juju-b71748-2
```

The slurm cluster is now prepared for further configuration and use in `License Manager` development.

## 2. Compose the License Manager API
Setting up the `License Manager API` for development is done in three steps:

1. Clone the project to your local machine
2. Run `make local`
3. Initialize the database with a license configuration for testing.

To get started, clone the `license-manager` repository from GitHub and run `make local`.

``` bash
git clone https://github.com/omnivector-solutions/license-manager
cd license-manager/lm-api
make local
```

We should now see two running docker containers; `lm-api-license-manager-1` and `lm-api-pgsql-1`.

`docker ps` shows:

``` bash
$ docker ps
CONTAINER ID   IMAGE                    COMMAND                  CREATED          STATUS                PORTS                    NAMES
ff6fcdcc7fdc   lm-api-license-manager   "uvicorn lm_api.main…"   40 seconds ago   Up 35 seconds         0.0.0.0:7000->8000/tcp   lm-api-license-manager-1
095cdd03027e   postgres:13-alpine       "docker-entrypoint.s…"   2 weeks ago      Up 4 days (healthy)   0.0.0.0:5433->5432/tcp   lm-api-test-db-1
32c70f6fb586   postgres:13-alpine       "docker-entrypoint.s…"   2 weeks ago      Up 4 days (healthy)   0.0.0.0:5432->5432/tcp   lm-api-pgsql-1
```

From the output above, we see that port `7000` on our local machine is forwarded to the listening port of the `License Manager API`
container (port `8000`). This means we will make requests to our local host IP address at port `7000` in order to access the `License Manager API` HTTP endpoints.

Now initialize the API with the following resources that we can use for testing:

1. Product
2. Configuration (with Feature and License Server included)

``` bash
PRODUCT_ID=$(curl -X 'POST' \
  'http://'$MY_IP':7000/lm/products/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "test_product"
  }' | jq '.id')


curl -X 'POST' \
  'http://'$MY_IP':7000/lm/configurations/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Test License",
  "cluster_client_id": "osd-cluster",
  "features": {
    "name": "test_feature",
    "product_id": '$PRODUCT_ID',
    "reserved": 0
  },
  "license_servers": {
    "host": $MY_IP,
    "port": 8000
  },
  "grace_time": 300,
  "type": "flexlm"
}
```

You can check that the resources were successfully added by making a request to list the configurations in the database (this
list should contain the license you previously added).

``` bash
curl -X 'GET' \
  'http://'$MY_IP':7000/lm/configurations' \
  -H 'accept: application/json'
```

``` bash
[
  {
    "id": 1,
    "name": "Test License",
    "cluster_client_id": "osd-cluster",
    "features": [
      {
        "id": 1,
        "name": "test_feature",
        "product": {
          "id": 1,
          "name": "test_product"
        },
        "config_id": 1,
        "reserved": 0,
        "total": 0,
        "used": 0
      }
    ],
    "license_servers": [
      {
        "id": 1,
        "config_id": 1,
        "host": 127.0.0.1,
        "port": 8000
      }
    ],
    "grace_time": 300,
    "type": "flexlm"
  }
]
```

The `License Manager API` is now configured and ready for use in the development environment.

## 3. Compose the License Manager Simulator
To run the `License Manager Simulator` API, enter the directory `lm-simulator-api` and run `make local`.

``` bash
cd license-manager/lm-simulator-api
make local
```

The `License Manager Simulator` API is now running and listening on port `8000`. You need to add the license created in the `License Manager API`
into the `License Manager Simulator API`. The license name should match the feature name created previously.

``` bash
curl -X 'POST' \
  'http://'$MY_IP':8000/lm-sim/licenses/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "test_feature",
  "total": 1000,
  "license_server_type": "flexlm"
}'
```

## 4. Add the License Manager Agent to the cluster
The final component we need to deploy is the `License Manager Agent`. The `License Manager Agent` is deployed to the
same model as the slurm charms, and related to `slurmctld`.

``` bash
git clone git@github.com:omnivector-solutions/charm-license-manager-agent
cd charm-license-manager-agent/
make charm
```

The `make charm` command will produce a resultant charm artifact named
`license-manager-agent.charm`. This is the charm that we will deploy.

Before deploying the charm, create a `yaml` configuration file that contains the needed settings for the
`License Manager Agent Charm`. The config should look something like this:

``` yaml
license-manager-agent:
  log-level: DEBUG
  stat-interval: 30
  license-manager-backend-base-url: "http://"$MY_IP":7000"
  lmutil-path: "/usr/local/bin/lmutil"
  rlmutil-path: "/usr/local/bin/rlmutil"
  lsdyna-path: "/usr/local/bin/lstc_qrun"
  lmxendutil-path: "/usr/local/bin/lmxendutil"
  olixtool-path: "/usr/local/bin/olixtool"
  dslicsrv-path: "/usr/local/bin/dslicsrv"
  oidc-domain: "your-oidc-domain"
  oidc-client-id: "your-oidc-client-id"
  oidc-client-secret: "your-oidc-client-secret"
  sentry-dsn: ""
```

Make sure to substitute the correct values into the new `license-manager-agent.yaml` configuration file
(especially the IP address of your host machine). You'll also need to provision an OIDC instance to authenticate
against the backend API.

Now that we have the charm artifact (`license-manager-agent.charm`) and
the config file for the charm (`license-manager-agent.yaml`), we are ready to deploy.

Using `juju`, deploy the `license-manager-agent` charm to the model, specifying the config file as an argument to the
deploy command.

``` bash
juju deploy ./license-manager-agent.charm \
    --config ./license-manager-agent.yaml --series focal
```

After the deploy, make sure to relate the charm to the juju-info and prolog-epilog interface.

``` bash
juju relate license-manager-agent:juju-info slurmctld
juju relate license-manager-agent:prolog-epilog slurmctld
```

## 5. Additional Modifications
At this point you should have 3 systems running:

1. Slurm cluster in LXD
2. License Manager Simulator API
3. License Manager API

Once the systems have been successfully deployed you will need to apply the post deployment configurations.
These configurations will ensure that your slurm cluster has a fake license server client and available licenses
to be used by the fake application (which will be run as a batch script).

### Configuring the license server client
The `License Manager Simulator` has a script for each license server supported (FlexLM, RLM, LS-Dyna, LM-X, OLicense and DSLS).
The script requests license information from the `License Manager Simulator API` and renders
it in a template, simulating the output from the real license server.

To configure it, you need to install the `License Manager Simulator` package inside the same virtual environment created for `License Manager Agent`.

By default, the `License Manager Agent` uses the virtual environment located at `/srv/license-manager-agent-venv`.
To install the `License Manager Simulator` package, run the following command:

``` bash
juju ssh license-manager-agent/0
source /srv/license-manager-agent-venv/bin/activate
pip install license-manager-simulator
```

After installing the License Manager Simulator, you need to update the configuration to use the path for the created binaries.

``` bash
juju config license-manager-agent lmutil-path=/srv/license-manager-agent-venv/bin/lmutil
juju config license-manager-agent rlmutil-path=/srv/license-manager-agent-venv/bin/rlmutil
juju config license-manager-agent lsdyna-path=/srv/license-manager-agent-venv/bin/lstc_qrun
juju config license-manager-agent lmxendutil-path=/srv/license-manager-agent-venv/bin/lmxendutil
juju config license-manager-agent olixtool-path=/srv/license-manager-agent-venv/bin/olixtool
juju config license-manager-agent dslicsrv-path=/srv/license-manager-agent-venv/bin/dslicsrv
```

### Configuring the Slurm license counter
You need to add a license counter to Slurm to match the license created in the `License Manager API` and the `License Manager Simulator API`.

To do this, you need to add the following configuration to the `slurmdctld` machine:

``` bash
juju ssh slurmctld/0
sudo sacctmgr add resource Type=license Clusters=osd-cluster Server=flexlm Names=test_product.test_feature Count=1000 ServerType=flexlm PercentAllowed=100 -i
```

### Using the simulated license server
You should now have a license for testing available. To check the output of the simulated license server, you can run:

``` bash
juju ssh license-manager-agent/0
/srv/license-manager-agent-venv/bin/lmutil lmstat -c 8000@127.0.0.1 -f test_Feature
```

The output should display the "test_product.test_feature" license that was added to the `License Manager Simulator`:

``` bash
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

Users of test_feature:  (Total of 1000 licenses issued;  Total of 0 licenses in use)

  "test_product" v62.2, vendor: FakeLM

  floating license
```

### Seeding the batch script and fake application
To test the `License Manager`, you need to run a fake application that will request licenses from the `License Manager Simulator` API,
and a batch script that will schedule the fake application job in the slurm cluster.

The fake application makes a request to the `License Manager Simulator` API to book 42 `test_feature` licenses, sleeps for a few seconds, and then deletes the booking.
The batch script will be responsible for scheduling the fake application job in the slurm cluster.

To run it, you need to modify the IP address in the `application.sh` file to match the IP where the `License Manager Simulator API` is running.

After that, copy the files to the `/tmp` directory in the `slurmd` machine.

To run the job, use the `sbatch` command.

``` bash
juju ssh slurmd/0 sbatch /tmp/batch.sh
```

## 6. Validation
After following the steps above, you should have a working development environment.
To validate that it is indeed working, submit a job to slurm (using the batch script) and check `License Manager API`.

Make a request to the `features` endpoint.

``` bash
curl -X 'GET' \
  'http://'$MY_IP':7000/lm/features' \
  -H 'accept: application/json'
```

You should see that the `used` value for the license was updated with the value used in the job (42).

``` bash
[
  {
    "id": 1,
    "name": "test_feature",
    "product": {
      "id": 1,
      "name": "test_product"
    },
    "config_id": 1,
    "reserved": 0,
    "total": 1000,
    "used": 42,
    "booked_total": 0
    }
]
```

You also should have a new job created. To verify this, make a request to the `jobs` endpoint.

``` bash
curl -X 'GET' \
  'http://'$MY_IP:7000'/lm/jobs' \
  -H 'accept: application/json'
```

The job should contain information about the job and also how many licenses were booked by the job.

``` bash
[
  {
    "id": 1,
    "slurm_job_id": "1",
    "cluster_client_id": "osd-cluster",
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
```

Wait for a few seconds (for the reconcile to run) and check again. The job and the booking should be deleted
and the `used` value will return to its original quantity.
