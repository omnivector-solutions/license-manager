# License Manager Agent Changelog

This file keeps track of all notable changes to `License Manager Agent`.

## Unreleased


## 3.3.0 -- 2024-05-30
* Fix bug in extraction of the lead host when the job runs in multiple nodes [ASP-5048]

## 3.2.0 -- 2024-04-29
* Improve FlexLM, LM-X and OLicense parsers to parse multiple versions of the license server output [ASP-4670]
* Fix LS-Dyna parser to parse the queue value when it's represented as a dash instead of a zero
* Fix bug with output parsing when there's non UTF-8 characters in the output [ASP-5160]
* Create service to clean the bookings once the license is checked out from the license server [ASP-4902]

## 3.1.0 -- 2024-01-24
* Updated linter and checker to use ruff [ASP-4293]
* Change minimum Python version to 3.12 [ASP-4294]
* Rename `agent` project to `lm-agent`

## 3.0.12 -- 2023-12-15
* Update reservation calculation to remove the reserved (limit) value [ASP-4349]

## 3.0.11 -- 2023-12-12
* Add support to Python 3.12

## 3.0.10 -- 2023-11-07
* Bumped version to keep in sync with backend

## 3.0.9 -- 2023-09-28
* Fix issue with clean jobs arguments not being passed to the function
* Remove timeout from backend client to avoid issues with long running requests

## 3.0.8 -- 2023-09-20
* Change reconciliation to fully reserve licenses when the license server doesn't respond

## 3.0.7 -- 2023-09-14
* Update logic to fetch bookings for all jobs using one request

## 3.0.6 -- 2023-08-29
* Fix bug when retrieving bookings for non existing job

## 3.0.5 -- 2023-08-29
* Change payload for feature update to include the product name 

## 3.0.4 -- 2023-08-28
* Improve function to get bookings sum from backend
* Improve function to get used values from cluster
* Updated reconciliation to update all features with one request
* Fix RLM parser to handle multiple features in the same license server

## 3.0.3 -- 2023-08-17
* Bumped to keep in sync with backend

## 3.0.2 -- 2023-08-14
* Bumped version to keep in sync with backend

## 3.0.1 -- 2023-08-10
* Bumped version to keep in sync with backend

## 3.0.0 -- 2023-08-08
* Refactored agent to use new API

## 2.3.2 -- 2023-06-08
* Fix regex bug on scontrol show lic parser

## 2.3.1 -- 2023-04-28
* Fixed unclosed async client warning message

## 2.3.0 -- 2023-03-06
* Changed the reconciliation method to use reservations instead of modifying the total of licenses

## 2.2.22 -- 2023-02-23
* Fixed RLM command line parameters

## 2.2.21 -- 2023-02-23
* Fixed issue with command parameters in server interfaces

## 2.2.20 -- 2023-02-07
* Bumped version to keep in sync with backend

## 2.2.19 -- 2023-02-01
* Bumped version to keep in sync with backend

## 2.2.18 -- 2023-01-26
* Added fallback in reconciliation to parse old feature format for retroactive compatibility

## 2.2.17.1 -- 2023-01-26
* Added Slurm reservation module with CRUD operations for reservations

## 2.2.17 -- 2023-01-24
* Bumped version to keep in sync with backend and lm-cli

## 2.2.16 -- 2022-11-22
* Updated configuration row to use new feature quantities format
* Added OLicense license server support

## 2.2.15 -- 2022-10-26
* Updated route to fetch licenses' configuration to use cluster specific route

## 2.2.14 -- 2022-10-03
* Bumped version to keep in sync with lm-cli

## 2.2.13 -- 2022-09-06
* Bumped version to keep in sync with backend

## 2.2.12 -- 2022-09-06
* Update backend configuration row schema to include new client_id field
* Patch code to fit Keycloak's authentication endpoints

## 2.2.11 -- 2022-07-11
* Keep version synced with the API

## 2.2.10 -- 2022-06-29
* Changed DEPLOY_ENV setting to a string (can now take arbitrary values)

## 2.2.9 -- 2022-06-06
* Implement async calls to license servers to fetch information in parallel

## 2.2.8 -- 2022-05-16
* Update RLM integration to use the same feature name displayed in the license server

## 2.2.7 -- 2022-05-03
* Filter cluster update response to only update licenses in the cluster

## 2.2.6 -- 2022-05-03
* Fixed local licenses filtering

## 2.2.5 -- 2022-04-04
* Fixed parsers to output feature name in lowercase
* Change Prolog and Epilog scripts to get job's license from env var instead of scontrol
* Add env var to flag if reconciliation should be triggered during Prolog and Epilog scripts execution

## 2.2.4 -- 2022-03-03
* Add LS-Dyna license server support
* Add LM-X license server support

## 2.2.3 -- 2022-02-09
* Fixed permission error when accessing cached token

## 2.2.2 -- 2022-02-03
* Bump to sync with lm-backend version

## 2.2.1 -- 2022-02-03
* Removed version check from backend
* Adjusted default token cache dir

## 2.2.0 -- 2022-02-02
* Refactored license_report module
* Remove lmstat binary
* Get license server type from backend configuration row
* Fix rlmutil command path
* Added auth via Auth0 and removed static token logic

## 2.1.1 -- 2022-01-10
* Remove lmstat binary
* Raise exception for empty reports on reconciliation

## 2.1.0 -- 2021-12-09
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
