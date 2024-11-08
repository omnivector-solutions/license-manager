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

<h3 align="center">License Manager Composed</h3>

<p align="center">
  A complete environment to do integration testing in License Manager.
  <br />
</p>


# About the Project

The `License Manager Composed` is a `docker-compose` project that allows you to run the `License Manager` components
in a local environment.

This is useful for development and integration testing purposes.

 ## Components

The `License Manager Composed` environment includes:

- `Slurm`
- `License Manager API`
- `License Manager Simulator API`
- `License Manager Agent`
- `License Manager Simulator`
- `Keycloak`

## Instructions

1. Start the environment:

```bash
docker compose up --build
```

2. Log into the `slurmctld` container:

```bash 
docker exec -it slurmctld bash
```

3. Execute the job example:

```bash
sbatch /nfs/job_example.py
```

The job will request a license to the `License Manager Simulator API` and return it after a few minutes.
It will be submitted to the Slurm cluster and the `License Manager Agent` will make a booking request to the `License Manager API`.
The results will be available in the `slurm-fake-nfs` directory.


## Bugs & Feature Requests

If you encounter a bug or a missing feature, please
[file an issue][issues-url]


## License
Distributed under the MIT License. See the [LICENSE][license-url] file for details.


## Contact
Email us: [Omnivector Solutions][contact-us]
