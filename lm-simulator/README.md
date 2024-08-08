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

The `License Manager Simulator`is an application that simulates several license servers output for use in the development of applications which interface to the license servers.

It contains fake binaries that simulate the license servers output.

License servers supported:

* FlexLM
* RLM
* LS-Dyna
* LM-X
* OLicense

## Installation
```bash
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install license-manager-simulator
```
The scripts will be available inside the `bin` folder in the venv.


## Prerequisites
To use the License Manager Simulator you must have `Slurm` and License Manager Agent charms deployed with `Juju`.
Instructions for this can be found at the [License Manager documentation][docs-url].

For each license server supported, there's a script that requests license information to the simulator API and a template
where the data will be rendered.

You also need to add licenses to the Simulator API and to the Slurm cluster, and then copy an application file to the `slurmd` node to run a job.


## Usage
There is an `application.sh` script that is intended to run in Slurm as a job that uses the licenses from the Simulator API. It is just a dummy
application for testing purposes that creates a `license_in_use` in the API, sleeps, then deletes the `license_in_use`.
There is also a `batch.sh` script to run the application via `sbatch`.

These files need to be updated with the Simulator API IP address provided in the step above before being copied to the `/tmp` folder in the `slurmd` node.

To submit the job, run:

```bash
$ juju ssh slurmd/leader sbatch /tmp/batch.sh
```

## License
Distributed under the MIT License. See the [LICENSE][license-url] file for details.


## Contact
Email us: [Omnivector Solutions][contact-us]
