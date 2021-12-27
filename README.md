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
    <a href="https://github.com/omnivector-solutions/license-manager/issues">
        Report Bug
    </a>
    ·
    <a href="https://github.com/omnivector-solutions/license-manager/issues">
        Request Feature
    </a>
  </p>
</p>


## Table of Contents

- [Table of Contents](#table-of-contents)
- [About The Project](#about-the-project)
- [Installation (backend)](#installation-backend)
- [Installation (agent)](#installation-agent)
- [Run locally](#run-locally)
- [Database Migrations](#database-migrations)
    - [Create Migrations](#create-migrations)
    - [Apply Migrations](#apply-migrations)
- [Test with lm-configure](#test-with-lm-configure)
- [License](#license)
- [Contact](#contact)


## About The Project

`license-manager` is a license scheduling middleware that adds value in situations where
multiple clusters share a license server or set of license servers.

The license-manager software consists of:
* the license-manager backend web server
* the license-manager agent (prolog and epilog scripts for Slurmd).


## Installation

To install, clone from github and run the install command:

```
git clone git@github.com:omnivector-solutions/license-manager
cd license-manager
make install
```


## Run locally

To run the backend locally, use `docker-compose` to run the application and its database
inside containers:

```
cd license-manager/backend
docker-compose up --build
```


## Database Migrations
The license manager project uses alembic to manage the database and perform migrations.
The migrations are kept in this project in the `alembic/versions` directory, and the
config file is in the root of the project, `alembic.ini`.


#### Create Migrations

To create a migration:

```bash
alembic revision -m "some comment" --autogenerate
```
Running the command above will create a revision file in `alembic/versions`,
(i.e. "b692dfd0b017_initial_revision.py")
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

In order to use this utility, first retrieve the required configuration settings
for authorization via Auth0. These may be retrieved from the Auth0 machine-to-manchine
app that you have configured for license-manager-agent. The four required values are:

* LM_AGENT_AUTH0_DOMAIN
* LM_AGENT_AUTH0_AUDIENCE
* LM_AGENT_AUTH0_CLIENT_ID
* LM_AGENT_AUTH0_CLIENT_SECRET

You will also need to set the location of the backend API. If you are running locally,
this will simply be `http://localhost:7000`. Bind this setting with:

* LM2_AGENT_BACKEND_BASE_URL

You may either bind these values by setting environment variables or by creating a
"dotenv" file with these values. Either way, they will be read by the agent at execution
time.

To test with the `lm-configure` cli run the following commands from the `agent` folder:

```bash
cd agent
poetry run lm-configure --help
```

To see all available configurations, run:

```bash
poetry run lm-configure get-all
```

To get one configuration row based on an ID:

```bash
poetry run lm-configure get [ID]
```

To add a configuration:

```bash
poetry run lm-configure add 100 "testproduct" ["Testfeature"] ["testserver"] "testservertype" 10000
```

To update a configuration:

```bash
poetry run lm-configure update 100 --[OPTION] [VALUE-TO-UPATE] ..
```

To delete a configuration row based on an ID:

```bash
poetry run lm-configure delete ID
```


## Making releases for the sub-projects

The sub-projects of the license-manager are released independently of each other.  When
releasing the sub-project, a tag for the release will be created that includes the name
of the sub-project.


### Release Process Overview

There are scripts to aid in the release process. However, knowing the process is useful.
Here is an overview assuming that the new release version should be "X.Y.Z":

* Pre-release
  * Make sure all changes for a release must have been merged into the main branch
  * Make sure the CHANGELOG includes each significant change in the `Unreleased` section
  * Identify whether the new version should be a Major, Minor, or Patch release
  * Increment the current version number accordingly
  * This is your target release `X.Y.Z`
* Prepare
  * From the main branch, check out a new branch titled `release/X.Y.Z`
  * Change the package version in the sub-project's `pyproject.toml`
  * Move the `Unreleased` items in the project's `CHANGELOG.rst` to a new release section
  * Commit the changes to `pyproject.toml` and `CHANGELOG.rst`, and push to origin
  * Create a pull-request for merging the changes into main
* Review
  * Get approval for the pull-request and merge
* Publish
  * Create a tag titled `X.Y.Z` and push it to origin
  * Publish the new version with poetry to pypicloud


### Using the scripts
There are two scripts and associated Make targets for the prepare and publish steps.

First, invoke the `prepare` script like so:

```bash
make prepare-<scope>  # where scope is one of 'major', 'minor', or 'patch'
```

If one of the pre-conditions described in the "pre-release" process is not fulfilled,
the script will fail and tell you why.

Once you have secured approval for the release and merged the changes to main, invoke
the `publish` script like so:

```bash
make publish
```


## License
Distributed under the MIT License. See `LICENSE` for more information.


## Contact
Omnivector Solutions - [www.omnivector.solutions][website] - <info@omnivector.solutions>
