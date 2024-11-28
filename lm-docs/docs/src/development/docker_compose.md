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
docker-compose up --build
```

The `docker compose` command will start the following services:

1. License Manager API
2. Postgresql database (for the License Manager API)
4. Keycloak (authentication provider for the-LM API)
5. License Manager Simulator API
6. Postgresql database (for the License Manager Simulator API)
7. Slurm cluster (Slurmctld, Slurmdbd, Slurmrestd, and two Slurmd containers)

## Submitting a job
1. Log into the `slurmctld` container:

```bash 
docker compose exec slurmctld bash
```

2. Execute the job example:

```bash
sbatch /nfs/job_example.py
```

The job will request 42 licenses to the `License Manager Simulator API` and return it after a few minutes.
It will be submitted to the Slurm cluster and the `License Manager Agent` will make a booking request to the `License Manager API`.
The results will be available in the `slurm-fake-nfs` directory.
