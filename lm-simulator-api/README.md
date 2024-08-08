[contributors-url]: https://github.com/omnivector-solutions/license-manager/graphs/contributors
[forks-url]: https://github.com/omnivector-solutions/license-manager/network/members
[stars-url]: https://github.com/omnivector-solutions/license-manager/stargazers
[issues-url]: https://github.com/omnivector-solutions/license-manager/issues
[license-url]: https://github.com/omnivector-solutions/license-manager/blob/master/LICENSE
[docs-url]: https://omnivector-solutions.github.io/license-manager/
[contact-us]: mailto:info@omnivector.solutions

[Contributors][contributors-url] •
[Forks][forks-url] •
[Stargazers][stars-url] •
[Issues][issues-url] •
[MIT License][license-url] •
[Documentation][docs-url] •
[Contact Us][contact-us] •

<!-- PROJECT LOGO -->
> An [Omnivector](https://www.omnivector.io/) initiative
>
> [![omnivector-logo](https://omnivector-public-assets.s3.us-west-2.amazonaws.com/branding/omnivector-logo-text-black-horz.png)](https://www.omnivector.io/)

<h3 align="center">License Manager Simulator</h3>

<p align="center">
  A License management simulator project for testing license integration in user applications.
  <br />
</p>


## About The Project

The `License Manager Simulator API`is an REST API that simulates a license server data for use in the development of applications which interface to the license servers.

License servers supported:

* FlexLM
* RLM
* LS-Dyna
* LM-X
* OLicense

## Installation
To install this project, clone the repository and use `docker-compose` to run it in containers:

```bash
$ cd lm-simulator-api
$ docker-compose up
```

This will create a container for the API, and also a PostgreSQL container for the database.

The API will be available at `http://localhost:8000/lm-sim`.

## Prerequisites
To use the License Manager Simulator API you must have License Manager Simulator scripts deployed together with a running License Manager Agent.

Instructions for this can be found at the [License Manager documentation][docs-url].

## Usage
You can add/remove licenses from the license server API using the online interface at `http://localhost:8000/lm-sim/docs`. This helps you to make requests directly with the browser into the API, with examples.

Make sure the license name in the API matches the feature name of your license in Slurm and in the License Manager API configuration.

For example:

License Manager Simulator API:
```
{
  "name": "abaqus",
  "type": "flexlm",
  "total": 1000
}
```

Slurm:
```
LicenseName=abaqus.abaqus@flexlm
  Total=1000 Used=0 Free=1000 Reserved=0 Remote=yes
```

License Manager API configuration:
```
{
  "id": 1,
  "name": "Abaqus",
  "cluster_client_id": "client_id",
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
      "total": 0,
      "used": 0,
      "booked_total": 0
    }
  ],
  "license_servers": [
    {
      "id": 1,
      "config_id": 1,
      "host": "localhost",
      "port": 8000
    }
  ],
  "grace_time": 300,
  "type": "flexlm"
}
```

The API IP address should go into the license server section of the configuration to ensure the scripts can communicate with the API.

## License
Distributed under the MIT License. See the [LICENSE][license-url] file for details.


## Contact
Email us: [Omnivector Solutions][contact-us]
