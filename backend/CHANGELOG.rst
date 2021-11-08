============
 Change Log
============

This file keeps track of all notable changes to license-manager-backend

Unreleased
----------
* Added Dockerfiles and docker-compose (for local development)
* Separated ``backend`` code from ``agent`` code into separate sub-projects
* Added ``config`` table and ``config`` endpoints in backend
* Parse job run-time through squeue and corrected time parsing logic
* Added docstrings throughout codebase

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
  * Skip eplilog cleanup loop if there are no bookings
  * Moved support functions to cmd_utils
  * Epilog updates token count to account for bookings
  * Added PRODUCT_FEATURE_RX, ENCODING, and TOOL_TIMEOUT to settings
  * Update prolog to only track licenses that match the expected format
  * Added feature flags for "booked" and "product_feature"
  * Extra accounting to add used slurm licenses to the total
  * Added forced reconcilliation to the prolog
  * Added slurmctld prolog and epilog entrypoints.
