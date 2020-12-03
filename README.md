[contributors-url]: https://github.com/omnivector-solutions/license-manager/graphs/contributors
[forks-url]: https://github.com/omnivector-solutions/license-manager/network/members
[stars-url]: https://github.com/omnivector-solutions/license-manager/stargazers
[issues-url]: https://github.com/omnivector-solutions/license-manager/issues
[license-url]: https://github.com/omnivector-solutions/license-manager/blob/master/LICENSE
[website]: https://www.omnivector.solutions

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

The license-manager software consists of; 1) the license-manager web server, 2) the slurmctld prolog and epilog scripts.


The prolog and epilog scripts are contained within the license-manager snap. Install the license-manager snap on the node(s) running slurmctld and add the `slurm.conf` configuration for `SlurmctldProlog` and `SlurmctldEpilog`.

## Building license-manager
To build the license-manager snap, install [snapcraft](https://snapcraft.io).

    sudo snap install snapcraft --classic

Use snapcraft to build and install the snap.

    snapcraft --use-lxd

## Installation
Use the `snap install` command to install the built snap.

    sudo snap install license-manager_0.1_amd64.snap --dangerous

## Configuration
Aside from providing the slurmctld prolog and epilog, `license-manager` can run in `server` mode.

To run the `license-manager-server` configure the `snap.mode` to `server`:

    sudo snap set license-manager snap.mode=server

## Usage


## License
Distributed under the MIT License. See `LICENSE` for more information.


## Contact
Omnivector Solutions - [www.omnivector.solutions][website] - <info@omnivector.solutions>

Project Link: [https://github.com/omnivector-solutions/license-manager](https://github.com/omnivector-solutions/license-manager)
