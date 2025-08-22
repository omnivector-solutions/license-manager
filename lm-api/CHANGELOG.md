# License Manager API Changelog

This file keeps track of all notable changes to `License Manager API`.

## Unreleased


## 4.4.2 -- 2025-08-22
* Update keycloak token structure [[PENG-3064](https://app.clickup.com/t/18022949/PENG-3064)]

## 4.4.1 -- 2025-05-20
* Bumped version to keep in sync with agent

## 4.4.0 -- 2025-04-04
* Remove `pytest-freezegun` dependency [ASP-6607]
* Update Poetry to 2.1.2 [[PENG-2660](https://sharing.clickup.com/t/h/c/18022949/PENG-2660/74MSS3GD0FAHASJ)]

## 4.3.0 -- 2025-02-03
* Use `pydantic_extra_types.pendulum_dt` to parse the `last_reported` field in `ClusterStatusSchema`
* Adjusted the default values of Sentry's sample rates [[PENG-2592](https://sharing.clickup.com/t/h/c/18022949/PENG-2592/QQUQ1ABLAP6QSYX)]

## 4.2.0 -- 2024-11-18
* Fix lifespan initialization in FastAPI app
* Remove DomainConfig from Armasec client to pass the attributes directly

## 4.1.0 -- 2024-10-10
* Add support to DSLS license server

## 4.0.0 -- 2024-08-30
* Bumped version to keep in sync with agent

## 3.4.0 -- 2024-08-19
* Upgrade FastAPI version to *^0.111.0*
* Upgrade Uvicorn version to *^0.30.1*
* Upgrade python-dotenv to *^0.21.0*
* Upgrade Armasec to *^2.0.1*
* Upgrade py-buzz to *^4.1.0*
* Upgrade Pydantic to *^2.8.2* [[PENG-2280](https://sharing.clickup.com/t/h/c/18022949/PENG-2280/YUSOZKBIF96CZJ0)]
* Add *pydantic-settings* as a dependency
* Remove the audience setting [[PENG-2231](https://sharing.clickup.com/t/h/c/18022949/PENG-2231/T3PXA6KD1EH124G)]
* Add env var to set whether Armasec should use HTTPS or HTTP

## 3.3.0 -- 2024-05-30
* Add new endpoints to manage the cluster reports from the agent [ASP-4601]

## 3.2.0 -- 2024-04-29
* Expanded permission sets from view/edit to create/read/update/delete [PENG-2160]
* Added admin permission to allow for full access to all resources [PENG-2207]

## 3.1.0 -- 2024-01-24
* Update constraints to limit int fields to 2**31-1 [PENG-1438]
* Change minimum Python version to 3.12 [ASP-4290]
* Update Dockerfile to use image python:3.12-slim-bullseye [ASP-4290]
* Updated linter and checker to use ruff [ASP-4293]
* Rename `backend` project to `lm-api` [ASP-4291]
* Modernize the Dockerfile to use multi-stage builds [ASP-4292]

## 3.0.12 -- 2023-12-15
* Fix bug in Feature read method that was returning None for the booked_total field

## 3.0.11 -- 2023-12-12
* Add support to Python 3.12

## 3.0.10 -- 2023-11-07
* Add constraints to schemas to ensure the correct values are used
* Optimized queries for feature list

## 3.0.9 -- 2023-09-28
* Bumped version to keep in sync with agent

## 3.0.8 -- 2023-09-20
* Bumped version to keep in sync with agent

## 3.0.7 -- 2023-09-14
* Updated /configurations update endpoint to update features and license servers related to the configuration

## 3.0.6 -- 2023-08-29
* Bumped version to keep in sync with agent

## 3.0.5 -- 2023-08-29
* Improved feature filtering by name and client_id by using the product name in the filter

## 3.0.4 -- 2023-08-28
* Added route /features/bulk to update multiple features in a single request

## 3.0.3 -- 2023-08-17
* Updated /configurations create endpoint to accept a complete configuration (with features and license servers)

## 3.0.2 -- 2023-08-14
* Added total and used as sortable fields in /features route

## 3.0.1 -- 2023-08-10
* Fixed bug in /license_servers/types route and updated it to use authentication

## 3.0.0 -- 2023-08-08
* Refactored API to use a normalized database.
* New endpoints available:
  - /configurations
  - /license_servers
  - /products
  - /features
  - /jobs
  - /bookings
* Added support for multi-tenancy

## 2.3.1 -- 2023-04-28
* Added endpoint to query available license server types
* Added validators to check license server types in create/update for configs
* Updated Dockerfile to use Poetry 1.4.0

## 2.3.0 -- 2023-03-06
* Bumped version to keep in sync with agent

## 2.2.22 -- 2023-02-23
* Bumped version to keep in sync with agent

## 2.2.21 -- 2023-02-23
* Bumped version to keep in sync with agent

## 2.2.20 -- 2023-02-07
* Fixed issue with async lock by using an async loop to start uvicorn

## 2.2.19 -- 2023-02-01
* Updated the booking create endpoint to fix overbooking issues

## 2.2.18 -- 2023-01-26
* Updated the configuration format to make the limit optional

## 2.2.17.1 -- 2023-01-26
* Bumped to sync with lm-agent version

## 2.2.17 -- 2023-01-24
* Changed return code for configuration create endpoint to 201
* Improved message responses in configuration create and update endpoints
* Added new endpoint to get the version of the API

## 2.2.16 -- 2022-11-22
* Updated license configuration to include a limit of how many features can be booked

## 2.2.15 -- 2022-10-26
* Bump to sync with lm-agent version

## 2.2.14 -- 2022-10-03
* Bump to sync with lm-cli version

## 2.2.13 -- 2022-09-06
* Update configuration edit endpoint to allow the client id field to be updated

## 2.2.12 -- 2022-09-06
* Add cluster_id column to config table to identify which cluster the configuration applies to
* Added new route to fetch all configurations from a specific cluster
* Added new route to fetch license usage with booked information
* Updated the sort logic for license endpoint to enable sorting using all columns

## 2.2.11 -- 2022-07-11
* Added support for multiple domains in auth settings (for keycloak)

## 2.2.10 -- 2022-06-29
* Changed DEPLOY_ENV to a string (to accept arbitrary values)

## 2.2.7 -- 2022-05-10
* Update docker-compose to use postgresql instead of postgres
* Added search and sort to list endpoints.
* Skipped 2.2.6 to sync with agent

## 2.2.5 -- 2022-04-12
* Bump to sync with lm-agent version

## 2.2.2 -- 2022-02-03
* Fixed reconcile query

## 2.2.1 - 2022-02-03
* Removed version check endpoint

## 2.2.0 -- 2022-02-02
* Simplified the permissions structure to a view/edit model for each data model

## 2.1.5 -- 2022-01-13
* Refactored the Dockerfile

## 2.1.4 -- 2022-01-08
* Added a detail endpoint for bookings by ID
* Upgraded databases and sqlalchemy versions

## 2.1.3 - 2021-12-15
* Removed the "LM2_" prefix from the Settings class

## 2.1.2 - 2021-12-10
* Changed the CORS policy to allow origins from everywhere

## 2.1.1 - 2021-12-07
* Restored mangum handler

## 2.1.0 -- 2021-12-06
* Added Dockerfiles and docker-compose (for local development)
* Separated `backend` code from `agent` code into separate sub-projects
* Added `config` table and `config` endpoints in backend
* Parse job run-time through squeue and corrected time parsing logic
* Added docstrings throughout codebase
* Changed backend structure: the previously app is now mounted as a subapp
* Removed unnecessary unit tests from the backend and refactored some from both backend and agent
* Added security via Armasec
* Removed lambda build and configuration items

## 1.0.0 -- 2021-06-03
* Enhanced logging with more debug information
* Added support for poetry to manage dependencies
* Added support for release to pypicloud
* Added authorization sub-project for security on AWS Lambda
* Vendorized flexlm
* Added support for deployment via terraform to AWS Lambda

* Backend:
  * Added alembic support
  * Added bookings endpoints
  * Added FastAPI app for backend

* Agent:
  * Skip epilog cleanup loop if there are no bookings
  * Moved support functions to cmd_utils
  * Epilog updates token count to account for bookings
  * Added PRODUCT_FEATURE_RX, ENCODING, and TOOL_TIMEOUT to settings
  * Update prolog to only track licenses that match the expected format
  * Added feature flags for "booked" and "product_feature"
  * Extra accounting to add used slurm licenses to the total
  * Added forced reconciliation to the prolog
  * Added slurmctld prolog and epilog entrypoints.

