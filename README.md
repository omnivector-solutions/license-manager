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
- [Prerequisites](#prerequisites)
- [Build](#build)
- [Installation](#installation)
- [Usage](#usage)
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
    make -B function.zip
    ```

2. Use the github
[omnivector-solutions/infrastructure][infrastructure] repository to deploy
this software. Follow the instructions in the infrastructure README.md to
install `terraform`.

    Live deployments should be configured in `live/license-manager/xxxx` (stage,
    prod, edge, or other).

    You will need to set one environment variable before running terraform:

    ```#!bash
    # a path to step 1 function.zip
    export TF_VAR_zipfile=/some/path/function.zip
    ```

    **RECOMMENDED**: Use your virtualenv `postactivate` script to set this environment
    variable every time you activate your virtualenv.


3. `terraform plan` and `terraform apply` can be used as normal.

    Terraform will output the live internet URL where you can access the HTTP API of the backend.


4. Run infrastructure tests.

    ```#!bash
    npm i
    npx bats deployment/test
    ```


## Deploy (agent)

TODO - snap/charm


## Run locally

```
# backend
uvicorn licensemanager2.backend.main:app
# agent
uvicorn licensemanager2.agent.main:app --port 8010
```



## License
Distributed under the MIT License. See `LICENSE` for more information.


## Contact
Omnivector Solutions - [www.omnivector.solutions][website] - <info@omnivector.solutions>

Project Link: [https://github.com/omnivector-solutions/license-manager](https://github.com/omnivector-solutions/license-manager)
