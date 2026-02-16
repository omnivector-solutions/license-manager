# Change Log

All notable changes to the License Manager project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## Unreleased

Refer to [changes](./changes) directory for unreleased changes.

<!-- towncrier release notes start -->

# [4.6.1](https://github.com/omnivector-solutions/license-manager/releases/tag/4.6.1) - 2026-02-16


## Agent

No significant changes.


## API

### Fixed

- Fixed issue in MetricsCollection database session, making it aware of multi-tenancy environments ([PR #494](https://github.com/omnivector-solutions/license-manager/pull/494))


## CLI

No significant changes.


## Simulator

No significant changes.


## Simulator API

No significant changes.


# [4.6.0](https://github.com/omnivector-solutions/license-manager/releases/tag/4.6.0) - 2026-02-13


## Agent

### Added

- Added towncrier as CHANGELOG manager ([PR #482](https://github.com/omnivector-solutions/license-manager/pull/482))

### Changed

- Migrated the project management tool from Poetry to uv ([PR #481](https://github.com/omnivector-solutions/license-manager/pull/481))

### Fixed

- Fixed FlexLM parser to parse "license" in the singular ([PR #483](https://github.com/omnivector-solutions/license-manager/pull/483))


## API

### Added

- Added towncrier as CHANGELOG manager ([PR #482](https://github.com/omnivector-solutions/license-manager/pull/482))
- Added a new /lm/metrics endpoint for Prometheus scrapers ([PR #485](https://github.com/omnivector-solutions/license-manager/pull/485))
- Added database indexes to improve metrics performance ([PR #486](https://github.com/omnivector-solutions/license-manager/pull/486))

### Changed

- Migrated the project management tool from Poetry to uv ([PR #481](https://github.com/omnivector-solutions/license-manager/pull/481))


## CLI

### Added

- Added towncrier as CHANGELOG manager ([PR #482](https://github.com/omnivector-solutions/license-manager/pull/482))

### Changed

- Migrated the project management tool from Poetry to uv ([PR #481](https://github.com/omnivector-solutions/license-manager/pull/481))


## Simulator

### Added

- Added towncrier as CHANGELOG manager ([PR #482](https://github.com/omnivector-solutions/license-manager/pull/482))

### Changed

- Migrated the project management tool from Poetry to uv ([PR #481](https://github.com/omnivector-solutions/license-manager/pull/481))


## Simulator API

### Added

- Added towncrier as CHANGELOG manager ([PR #482](https://github.com/omnivector-solutions/license-manager/pull/482))

### Changed

- Migrated the project management tool from Poetry to uv ([PR #481](https://github.com/omnivector-solutions/license-manager/pull/481))


## 4.5.0 -- 2025-11-14

### Agent

* Add exception treatment to server interfaces to ensure the next server will be reached if the first one fails to respond [ASP-6723]
* Check for timeout exceptions when running commands with subprocess
* Update dependencies to latest versions
* Improve `ruff` configuration for linting and formatting

### API

* Update keycloak token structure [PENG-3064]
* Update dependencies to latest versions
* Improve `ruff` configuration for linting and formatting

### CLI

* Update dependencies to latest versions
* Improve `ruff` configuration for linting and formatting

### Simulator

* Update dependencies to latest versions
* Improve `ruff` configuration for linting and formatting

### Simulator API

* Update dependencies to latest versions
* Improve `ruff` configuration for linting and formatting

---

## 4.4.0 -- 2025-04-04

### Agent

* Pin `APSCheduler` version to 3.10.4 to avoid breaking changes [ASP-6607]
* Update ``Poetry`` to 2.1.2 [PENG-2660]

### API

* Remove `pytest-freezegun` dependency [ASP-6607]
* Update `Poetry` to 2.1.2 [PENG-2660]

### CLI

* Update `Poetry` to 2.1.2 [PENG-2660]

### Simulator

* Update `Poetry` to 2.1.2 [PENG-2660]

### Simulator API

* Update `Poetry` to 2.1.2 [PENG-2660]

---

## 4.3.0 -- 2025-02-03

### Agent

* Updated Agent to find .env file [PENG-2499]
* Fix DSLS parser to handle outputs with a warning line [ASP-5422]
* Fix License Report module to generate the correct feature report when the get_report_item fails [ASP-5422]
* Update Sentry integration to send only CRITICAL events [PENG-2622]
* Added configuration settings for customising Sentry's sample rates [PENG-2592]

### API

* Use `pydantic_extra_types.pendulum_dt` to parse the `last_reported` field in `ClusterStatusSchema`
* Adjusted the default values of Sentry's sample rates [PENG-2592]

---

## 4.2.0 -- 2024-11-18

### API

* Fix lifespan initialization in FastAPI app
* Remove DomainConfig from Armasec client to pass the attributes directly

---

## 4.1.0 -- 2024-10-10

### Agent

* Add support to DSLS license server

### API

* Add support to DSLS license server

### Simulator

* Add support to DSLS license server

### Simulator API

* Add support to DSLS license server

---

## 4.0.0 -- 2024-08-30

### Agent

* Remove OIDC_AUDIENCE setting
* Change .env prefix to LM_AGENT in settings
* Convert the reconciliation from a systemd timed service into a running process [ASP-5382]

### CLI

* Remove OIDC_AUDIENCE setting

### Simulator

* Added README link to PyPI page

### Simulator API

* Added version number to documentation page
* Added README link to PyPI page

---

## 3.4.0 -- 2024-08-19

### Agent

* Add env var to set wheter the agent should use HTTP or HTTPS to communicate with the OIDC provider
* Fix FlexLM parser to parse an output with only one license checked out
* Upgrade Pydantic to ^2.7.4 [PENG-2281]
* Add pydantic-settings as a dependency

### API

* Upgrade FastAPI version to ^0.111.0
* Upgrade Uvicorn version to ^0.30.1
* Upgrade python-dotenv to ^0.21.0
* Upgrade Armasec to ^2.0.1
* Upgrade py-buzz to ^4.1.0
* Upgrade Pydantic to ^2.8.2 [PENG-2280]
* Add pydantic-settings* as a dependency
* Remove the audience setting [PENG-2231]
* Add env var to set whether Armasec should use HTTPS or HTTP

### CLI

* Upgrade Pydantic to ^2.8.2

### Simulator

* Remove project from the Simulator API
* Update fake binaries to receive arguments from the command line
* Removed the filtering by name from the fake binaries
* Updated the templates to receive multiple licenses of the same type

### Simulator API

* Migrated the project to the main license-manager repository
* Upgrade FastAPI to ^0.111.0
* Upgrade Pydantic to ^2.8.2
* Added cascade delete to remove Licenses In Use when the License is deleted
* Refactored database module to use AsyncSesssion
* Converted job application example to Python
* Add LicenseServerType column to License table
* Add routes to filter by name and LicenseServerType

---

## 3.3.0 -- 2024-05-30

### Agent

* Fix bug in extraction of the lead host when the job runs in multiple nodes [ASP-5048]
* Update agent to report the cluster status to the API during the reconciliation [ASP-4603]

### API

* Add new endpoints to manage the cluster reports from the agent [ASP-4601]

---

## 3.2.0 -- 2024-04-29

### Agent

* Improve FlexLM, LM-X and OLicense parsers to parse multiple versions of the license server output [ASP-4670]
* Fix LS-Dyna parser to parse the queue value when it's represented as a dash instead of a zero
* Fix bug with output parsing when there's non UTF-8 characters in the output [ASP-5160]
* Create service to clean the bookings once the license is checked out from the license server [ASP-4902]

### API

* Expanded permission sets from view/edit to create/read/update/delete [PENG-2160]
* Added admin permission to allow for full access to all resources [PENG-2207]

---

## 3.1.0 -- 2024-01-24

### Agent

* Updated linter and checker to use `ruff` [ASP-4293]
* Change minimum Python version to 3.12 [ASP-4294]
* Rename `agent` project to `lm-agent`

### API

* Update constraints to limit int fields to 2**31-1 [PENG-1438]
* Change minimum Python version to 3.12 [ASP-4290]
* Update Dockerfile to use image `python:3.12-slim-bullseye` [ASP-4290]
* Updated linter and checker to use `ruff` [ASP-4293]
* Rename `backend` project to `lm-api` [ASP-4291]
* Modernize the Dockerfile to use multi-stage builds [ASP-4292]

### CLI

* Updated linter and checker to use `ruff` [ASP-4293]
* Change minimum Python version to 3.12 [ASP-4295]

---

## 3.0.12 -- 2023-12-15

### Agent

* Update reservation calculation to remove the reserved (limit) value [ASP-4349]

### API

* Fix bug in Feature read method that was returning None for the booked_total field

---

## 3.0.11 -- 2023-12-12

### Agent

* Add support to Python 3.12

### API

* Add support to Python 3.12

---

## 3.0.10 -- 2023-11-07

### API

* Add constraints to schemas to ensure the correct values are used
* Optimized queries for feature list

---

## 3.0.9 -- 2023-09-28

### Agent

* Fix issue with clean jobs arguments not being passed to the function
* Remove timeout from backend client to avoid issues with long running requests

---

## 3.0.8 -- 2023-09-20

### Agent

* Change reconciliation to fully reserve licenses when the license server doesn't respond

---

## 3.0.7 -- 2023-09-14

### Agent

* Update logic to fetch bookings for all jobs using one request

### API

* Updated /configurations update endpoint to update features and license servers related to the configuration

---

## 3.0.6 -- 2023-08-29

### Agent

* Fix bug when retrieving bookings for non existing job

---

## 3.0.5 -- 2023-08-29

### Agent

* Change payload for feature update to include the product name

### API

* Improved feature filtering by name and client_id by using the product name in the filter

---

## 3.0.4 -- 2023-08-28

### Agent

* Improve function to get bookings sum from backend
* Improve function to get used values from cluster
* Updated reconciliation to update all features with one request
* Fix RLM parser to handle multiple features in the same license server

### API

* Added route /features/bulk to update multiple features in a single request

---

## 3.0.3 -- 2023-08-17

### API

* Updated /configurations create endpoint to accept a complete configuration (with features and license servers)

---

## 3.0.2 -- 2023-08-14

### API

* Added total and used as sortable fields in /features route

---

## 3.0.1 -- 2023-08-10

### API

* Fixed bug in /license_servers/types route and updated it to use authentication

---

## 3.0.0 -- 2023-08-08

### Agent

* Refactored agent to use new API

### API

* Refactored API to use a normalized database.
* New endpoints available:

  * /configurations
  * /license_servers
  * /products
  * /features
  * /jobs
  * /bookings
* Added support for multi-tenancy

### CLI

* Refactored CLI to use new API

---

## 2.3.2 -- 2023-06-08

### Agent

* Fix regex bug on scontrol show lic parser

---

## 2.3.1 -- 2023-04-28

### API

* Added endpoint to query available license server types
* Added validators to check license server types in create/update for configs
* Updated Dockerfile to use `Poetry` 1.4.0

### Agent

* Fixed unclosed async client warning message

---

## 2.3.0 -- 2023-03-06

### Agent

* Changed the reconciliation method to use reservations instead of modifying the total of licenses

---

## 2.2.22 -- 2023-02-23

### Agent

* Fixed RLM command line parameters

---

## 2.2.21 -- 2023-02-23

### Agent

* Fixed issue with command parameters in server interfaces

---

## 2.2.20 -- 2023-02-07

### API

* Fixed issue with async lock by using an async loop to start uvicorn

---

## 2.2.19 -- 2023-02-01

### API

* Updated the booking create endpoint to fix overbooking issues

---

## 2.2.18 -- 2023-01-26

### API

* Updated the configuration format to make the limit optional

---

## 2.2.17.1 -- 2023-01-26

### Agent

* Added Slurm reservation module with CRUD operations for reservations

---

## 2.2.17 -- 2023-01-24

### API

* Changed return code for configuration create endpoint to 201
* Improved message responses in configuration create and update endpoints
* Added new endpoint to get the version of the API

### Agent

* Added Slurm reservation module with CRUD operations for reservations

### CLI

* Improved error message handling when a request to the API fails

---

## 2.2.16 -- 2022-11-22

### API

* Updated license configuration to include a limit of how many features can be booked

### Agent

* Updated configuration row to use new feature quantities format
* Added OLicense license server support

### CLI

* Updated configuration create command help text to include new configuration format
* Updated requests to the backend API to use full path for routes

---

## 2.2.15 -- 2022-10-26

### Agent

* Updated route to fetch licenses' configuration to use cluster specific route

---

## 2.2.14 -- 2022-10-03

### CLI

* Changed Python version to 3.6.2 for compatibility

---

## 2.2.13 -- 2022-09-06

### API

* Update configuration edit endpoint to allow the client id field to be updated

---

## 2.2.12 -- 2022-09-06

### Agent

* Update backend configuration row schema to include new client_id field

### API

* Add cluster_id column to config table to identify which cluster the configuration applies to
* Added new route to fetch all configurations from a specific cluster
* Added new route to fetch license usage with booked information
* Updated the sort logic for license endpoint to enable sorting using all columns

### CLI

* Created the project. Features: commands to list licenses, list bookings, list, create and delete configurations.
* Update license list command to include booked information in license usage table

---

## 2.2.11 -- 2022-07-11

### API

* Added support for multiple domains in auth settings (for keycloak)

---

## 2.2.10 -- 2022-06-29

### Agent

* Changed DEPLOY_ENV setting to a string (can now take arbitrary values)

### API

* Changed DEPLOY_ENV setting to a string (can now take arbitrary values)

---

## 2.2.9 -- 2022-06-06

### Agent

* Implement async calls to license servers to fetch information in parallel

---

## 2.2.8 -- 2022-05-16

### Agent

* Update RLM integration to use the same feature name displayed in the license server

---

## 2.2.7 -- 2022-05-10

### Agent

* Filter cluster update response to only update licenses in the cluster

### API

* Update docker-compose to use postgresql instead of postgres
* Added search and sort to list endpoints.
* Skipped 2.2.6 to sync with agent

---

## 2.2.6 -- 2022-05-03

### Agent

* Fixed local licenses filtering

---

## 2.2.5 -- 2022-04-12

### Agent

* Fixed parsers to output feature name in lowercase
* Change Prolog and Epilog scripts to get job's license from env var instead of scontrol
* Add env var to flag if reconciliation should be triggered during Prolog and Epilog scripts execution

---

## 2.2.4 -- 2022-03-03

### Agent

* Add LS-Dyna license server support
* Add LM-X license server support

---

## 2.2.3 -- 2022-02-09

### Agent

* Fixed permission error when accessing cached token

---

## 2.2.2 -- 2022-02-03

### API

* Fixed reconcile query

---

## 2.2.1 -- 2022-02-03

### Agent

* Removed version check from backend
* Adjusted default token cache dir

### API

* Removed version check endpoint

---

## 2.2.0 -- 2022-02-02

### Agent

* Refactored license_report module
* Remove lmstat binary
* Get license server type from backend configuration row
* Fix rlmutil command path
* Added auth via Auth0 and removed static token logic

### API

* Simplified the permissions structure to a view/edit model for each data model

---

## 2.1.5 -- 2022-01-13

### API

* Refactored the Dockerfile

---

## 2.1.4 -- 2022-01-08

### API

* Added a detail endpoint for bookings by ID
* Upgraded databases and sqlalchemy versions

---

## 2.1.3 -- 2021-12-15

### API

* Removed the "LM2_" prefix from the Settings class

---

## 2.1.2 -- 2021-12-10

### API

* Changed the CORS policy to allow origins from everywhere

---

## 2.1.1 -- 2021-12-07

### Agent

* Remove lmstat binary
* Raise exception for empty reports on reconciliation

### API

* Restored mangum handler

---

## 2.1.0 -- 2021-12-06

### API

* Added Dockerfiles and docker-compose (for local development)
* Separated `backend` code from `agent` code into separate sub-projects
* Added `config` table and `config` endpoints in backend
* Parse job run-time through squeue and corrected time parsing logic
* Added docstrings throughout codebase
* Changed backend structure: the previously app is now mounted as a subapp
* Removed unnecessary unit tests from the backend and refactored some from both backend and agent
* Added security via Armasec
* Removed lambda build and configuration items

### Agent

* Added RLM parser
* Converted agent to a CLI application (from FastAPI with internal scheduler)
* Update booking-accounting logic to requeue jobs if there are not enough licenses
* Added in-use cleanup logic
* Added grace-time cleanup logic
* Separated ``backend`` code from ``agent`` code into separate sub-projects
* Added ``config`` table and ``config`` endpoints in backend
* Parse job run-time through squeue and corrected time parsing logic
* Added docstrings throughout codebase
* Changed backend URL prefix

---

## 1.0.0 -- 2021-06-03

### Initial Release

* Enhanced logging with more debug information
* Added support for poetry to manage dependencies
* Added support for release to pypicloud
* Added authorization sub-project for security on AWS Lambda
* Vendorized flexlm
* Added support for deployment via terraform to AWS Lambda

### Agent

* Skip epilog cleanup loop if there are no bookings
* Moved support functions to cmd_utils
* Epilog updates token count to account for bookings
* Added PRODUCT_FEATURE_RX, ENCODING, and TOOL_TIMEOUT to settings
* Update prolog to only track licenses that match the expected format
* Added feature flags for "booked" and "product_feature"
* Extra accounting to add used slurm licenses to the total
* Added forced reconciliation to the prolog
* Added slurmctld prolog and epilog entrypoints.

### API

* Added alembic support
* Added bookings endpoints
* Added FastAPI app for backend

---

## 0.3.0 -- 2021-05-10

### Simulator API

* Fixed lm-sim ip in setup scripts to use the new subapp endpoint
* Renamed script and template files to match license servers' binary filename
* Created OLicense Generator

---

## 0.2.0 -- 2021-04-12

### Simulator API

* Created RLM Generator
* Created LS-Dyna Generator
* Created LM-X Generator
* Added setup scripts to copy license server binaries and fake Slurm job to cluster and add licenses to Slurm and lm-sim API
* Moved the API endpoints to a subapp in the URL http://<ip-address>:<port>/lm-sim

---

## 0.1.0 -- 2021-03-01

### Simulator API

* Created CLI app to produce simulated flexlm output (from data pulled from API)
* Added fake SLURM job to credit and debit licenses
* Added unit tests
* Added FastAPI app to serve create-licenses and licenses-in-use endpoints
* Added CRUD logic over postgres database
* Created FlexLM Generator (render template with configuration values)
* Added output template (example)
* Added basic documentation (README)
