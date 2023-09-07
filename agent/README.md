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

<h3 align="center">License Manager Agent</h3>

<p align="center">
  A Python agent that runs in a HPC system to manage license usage and license reservations.
  <br />
</p>


# About the Project

The `License Manager Agent` is responsible for keeping the local cluster license totals
in sync with the the 3rd party license server totals. It's also responsible for making booking requests
to the `License Manager API` when Slurm is configured to use the `PrologSlurmctld` script provided by `License Manager Agent`.


## Documentation

Please visit the
[License Manager Documentation][docs-url]
page for details on how to install and operate License Manager.


## Bugs & Feature Requests

If you encounter a bug or a missing feature, please
[file an issue][issues-url]


## License
Distributed under the MIT License. See the [LICENSE][license-url] file for details.


## Contact
Email us: [Omnivector Solutions][contact-us]
