============
 Change Log
============

This file keeps track of all notable changes to license-manager-agent

Unreleased
----------
* Implement async calls to license servers to fetch information in parallel

2.2.8 -- 2022-05-16
-------------------
* Update RLM integration to use the same feature name displayed in the license server

2.2.7 -- 2022-05-03
-------------------
* Filter cluster update response to only update licenses in the cluster

2.2.6 -- 2022-05-03
-------------------
* Fixed local licenses filtering

2.2.5 -- 2022-04-04
-------------------
* Fixed parsers to output feature name in lowercase
* Change Prolog and Epilog scripts to get job's license from env var instead of scontrol
* Add env var to flag if reconciliation should be triggered during Prolog and Epilog scripts execution

2.2.4 -- 2022-03-03
-------------------
* Add LS-Dyna license server support
* Add LM-X license server support

2.2.3 - 2022-02-09
* Fixed permission error when accessing cached token 

2.2.2 - 2022-02-03
------------------
* Bump to sync with lm-backend version

2.2.1 - 2022-02-03
------------------
* Removed version check from backend
* Adjusted default token cache dir

2.2.0 - 2022-02-02
------------------
* Refactored tokenstat module
* Remove lmstat binary
* Get license server type from backend configuration row
* Fix rlmutil command path
* Added auth via Auth0 and removed static token logic

2.1.1 - 2022-01-10
------------------
* Remove lmstat binary
* Raise exception for empty reports on reconciliation

2.1.0 - 2021-12-09
------------------
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

1.0.0 -- 2021-06-03
-------------------
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
