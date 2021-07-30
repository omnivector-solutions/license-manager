[contributors-url]: https://github.com/omnivector-solutions/license-manager/graphs/contributors
[forks-url]: https://github.com/omnivector-solutions/license-manager/network/members
[stars-url]: https://github.com/omnivector-solutions/license-manager/stargazers
[issues-url]: https://github.com/omnivector-solutions/license-manager/issues
[license-url]: https://github.com/omnivector-solutions/license-manager/blob/master/LICENSE
[website]: https://www.omnivector.solutions
[infrastructure]: https://github.com/omnivector-solutions/infrastructure

[Contributors][contributors-url] •
[Forks][forks-url] •
[Stargazers][stars-url] •
[Issues][issues-url] •
[MIT License][license-url] •
[Website][website]

<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/omnivector-solutions/license-manager">
    <img src=".images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">license-manager</h3>

  <p align="center">
    A License management middleware for HPC systems.
    <br />
    <a href="https://github.com/omnivector-solutions/license-manager/issues">Report Bug</a>
    ·
    <a href="https://github.com/omnivector-solutions/license-manager/issues">Request Feature</a>
  </p>
</p>

[![](https://github.com/omnivector-solutions/license-manager/workflows/TestBuildReleaseEdge/badge.svg)](https://github.com/omnivector-solutions/license-manager-simulator/actions?query=workflow%3ATestBuildReleaseEdge)

<!-- TABLE OF CONTENTS -->

## Table of Contents

- [Table of Contents](#table-of-contents)
- [About The Project](#about-the-project)
- [Installation (backend)](#installation-backend)
- [Installation (agent)](#installation-agent)
- [Deployment (backend)](#deployment-backend)
  - [NOTE: Destroying secrets with terraform](#note-destroying-secrets-with-terraform)
- [Deploy (agent)](#deploy-agent)
- [Run locally](#run-locally)
- [Database Migrations](#database-migrations)
    - [Create Migrations](#create-migrations)
    - [Apply Migrations](#apply-migrations)
- [Test with lm-configure](#test-with-lm-configure)
- [License](#license)
- [Contact](#contact)

<!-- ABOUT THE PROJECT -->

## About The Project
`license-manager` is a license scheduling middleware that adds value in situations where multiple clusters share a license server or set of license servers.

(FIXME) The license-manager software consists of; 1) the license-manager web server, 2) the slurmctld prolog and epilog scripts.

(FIXME) The prolog and epilog scripts are contained within the license-manager snap. Install the license-manager snap on the node(s) running slurmctld and add the `slurm.conf` configuration for `SlurmctldProlog` and `SlurmctldEpilog`.


## Installation (backend)

```
git clone git@github.com:omnivector-solutions/license-manager
python3 -m venv venv
. venv/bin/activate
pip install wheel .[dev]
```


## Installation (agent)

Follow the steps for Installation (backend) and you will have a checkout of
the agent, and its dependencies, as well.


## Deployment (backend)

1. Start by building the lambda zipfile:

    ```#!bash
    make -B function.zip function-jawthorizer.zip
    ```

2. Use the github
[omnivector-solutions/infrastructure][infrastructure] repository to deploy
this software. Follow the instructions in the infrastructure README.md to
install `terraform`.

    Live deployments should be configured in `live/license-manager/xxxx` (stage,
    prod, edge, or other).

    Before running terraform:

    ```#!bash
    # create scratch.auto.tfvars
    echo > scratch.auto.tfvars << EOF
    zipfile = "/some/path/to/function.zip"
    zipfile_authorizer = "/some/path/to/function-jawthorizer.zip"
    EOF

    ```


3. Run terraform commands:

    ```#!bash
    cd live/license-manager/xxxx  # plug in some stage or custom directory here

    # install the modules this terraform configuration will import (like pip install)
    terraform init

    # show what resources will be changed, like a dry run
    terraform plan -out lm.out

    # actually create/modify resources
    terraform apply lm.out
    ```

    Terraform will output the live internet URL where you can access the HTTP API of the backend.


4. Run infrastructure tests.

    ```#!bash
    npm i
    npx bats deployment/test
    ```

### NOTE: Destroying secrets with terraform

AWS holds destroyed secrets for 7-30 days (depending on how they're configured). So if you use
`terraform destroy` and then try to recreate the resources right away, AWS (via terraform) will tell you:

```
Error: error creating Secrets Manager Secret: InvalidRequestException: You can't create this 
secret because a secret with this name is already scheduled for deletion.
```

If you get this error, you can fix it by restoring and importing the old secret into terraform:

```
# use the aws cli to restore the secret
$ aws secretsmanager restore-secret --secret-id /license-manager/{{YOUR_STAGE_NAME}}/token-secret
{
    "Name": "/license-manager/cory/token-secret",
    "ARN": "arn:aws:secretsmanager:us-west-2:212021838531:secret:/license-manager/{{YOUR_STAGE_NAME}}/token-secret-xyzabc"
}


# import the restored secret back into terraform using the ARN of the restored secret
$ terraform import module.license-manager.module.apigw.module.token-authorizer[0].aws_secretsmanager_secret.token_secret  arn:aws:secretsmanager:us-west-2:212021838531:secret:/license-manager/{{YOUR_STAGE_NAME}}/token-secret-xyzabc

module.license-manager.module.apigw.module.token-authorizer[0].aws_secretsmanager_secret.token_secret: Importing from ID "arn:aws:secretsmanager:us-west-2:212021838531:secret:/license-manager/{{YOUR_STAGE_NAME}}/token-secret-xyzabc"...
module.license-manager.module.apigw.module.token-authorizer[0].aws_secretsmanager_secret.token_secret: Import prepared!
  Prepared aws_secretsmanager_secret for import
module.license-manager.module.apigw.module.token-authorizer[0].aws_secretsmanager_secret.token_secret: Refreshing state... [id=arn:aws:secretsmanager:us-west-2:212021838531:secret:/license-manager/{{YOUR_STAGE_NAME}}/token-secret-xyzabc]

Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.


# run terraform plan/apply as usual
$ terraform plan -out myplan.out
...
Plan: 1 to add, 1 to change, 0 to destroy.
```

In the last step, terraform will create any other resources that it needs to. It will also alter-in-place
and fix the secret so you can keep working.

## Deploy (agent)

TODO - pypi/charm


## Run locally

```
# backend
uvicorn licensemanager2.backend.main:app
# agent
uvicorn licensemanager2.agent.main:app --port 8010
```

## Database Migrations
The license manager project uses alembic to manage the database and perform migrations. 
The migrations are kept in this project in the `alembic/versions` directory, and the config file is in the root of the project, `alembic.ini`. 

#### Create Migrations
To create a migration:
```bash
alembic revision -m "some comment" --autogenerate
```
Running the command above will create a revision file in `alembic/versions`, (i.e. "b692dfd0b017_initial_revision.py")
The revision of this file will be the string prepended to the filename. 

#### Apply Migrations
To apply a migration:
```bash
alembic upgrade <revision> (or "head" for latest) 
```
Using the example above, upgrade command looks like this:
```bash
alembic upgrade b692dfd0b017
```

## Test with lm-configure
In order to use this utility, first create a jwt for your environemnt using:
```bash
lm-create-jwt --subject <any> --app-short-name license-manager --stage <stage> --region <region>
```
where region is equal to the aws region the backend is deployed (i.e. "eu-north-1"), stage is the name
of your environment, and subject is arbitrary.

Once the token is created, run the following commands to export it.
```bash
export LM2_AGENT_BACKEND_API_TOKEN=<token> (use output from above)
```
Export the `LM2_AGENT_BACKEND_BASE_URL' to point to your backend, substituting in your stage and region.
```bash
export LM2_AGENT_BACKEND_BASE_URL=https://license-manager-<stage>-<region>.omnivector.solutions
```

To test with the `lm-configure` cli run the following commands in the same environment
the backend is running.
To get all configurations:
```bash
lm-configure get-all
```
To get one configuration row based on an ID:
```bash
lm-configure get [ID]
```
To add a configuration:
```bash
lm-configure add 100 "testproduct" ["Testfeature"] ["testserver"] "testservertype" 10000
```
To update a configuration
```bash
lm-configure update 100 --[OPTION] [VALUE-TO-UPATE] ..
```
To delete a configuration row based on an ID:
```bash
lm-configure delete ID
```

## License
Distributed under the MIT License. See `LICENSE` for more information.


## Contact
Omnivector Solutions - [www.omnivector.solutions][website] - <info@omnivector.solutions>

Project Link: [https://github.com/omnivector-solutions/license-manager](https://github.com/omnivector-solutions/license-manager)
