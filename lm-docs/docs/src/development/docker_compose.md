# Using Docker Compose

## Pre-Installation
Before you get started, ensure you have the following pre-requisites installed on your machine:

* docker
* docker compose

## Running the License Manager Composed
To get started, clone the `license-manager` repository from GitHub and run `docker compose up`.

``` bash
git clone https://github.com/omnivector-solutions/license-manager
cd license-manager/lm-composed
docker compose up --build
```

The `docker compose` command will start the following services:

1. License Manager API
2. Postgresql database (for the License Manager API)
3. License Manager Simulator API
4. Postgresql database (for the License Manager Simulator API)
5. License Manager Agent
6. Keycloak (authentication provider for the LM API)
7. Slurm cluster (Slurmctld, Slurmdbd, Slurmrestd, and two Slurmd containers)

The `License Manager Agent` runs as its own container, decoupled from the `slurmctld` container. The `slurmctld` container only has the
`License Manager Prolog/Epilog` scripts installed, which are configured to communicate directly with the `License Manager API`.

## Submitting a job
1. Log into the `slurmctld` container:

```bash 
docker exec -it slurmctld bash
```

2. Execute the job example:

```bash
sbatch /nfs/job_example.py
```

The job will request 42 licenses to the `License Manager Simulator API` and return it after a few minutes.
It will be submitted to the Slurm cluster and the `License Manager Prolog` script will make a booking request to the `License Manager API`.
The results will be available in the `slurm-fake-nfs` directory.
