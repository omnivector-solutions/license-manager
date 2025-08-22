# Change Log

This file keeps track of all notable changes to License Manager Simulator API

## Unreleased


## 4.4.2 -- 2025-08-22
* Bumped version to keep in sync with LM-API

## 4.4.1 -- 2025-05-20
* Bumped version to keep in sync with agent

## 4.4.0 -- 2025-04-04
* Update Poetry to 2.1.2 [[PENG-2660](https://sharing.clickup.com/t/h/c/18022949/PENG-2660/74MSS3GD0FAHASJ)]

## 4.3.0 -- 2025-02-03
* Bumped version to keep in sync with LM-API and LM-Agent

## 4.2.0 -- 2024-11-18
* Bumped version to keep in sync with LM-API

## 4.1.0 -- 2024-10-10
* Add support to DSLS license server


## 4.0.0 -- 2024-08-30
* Added version number to documentation page
* Added README link to PyPI page

## 3.4.0 -- 2024-08-19
* Migrated the project to the main license-manager repository
* Upgrade FastAPI to *^0.111.0*
* Upgrade Pydantic to *^2.8.2*
* Added cascade delete to remove Licenses In Use when the License is deleted
* Refactored database module to use AsyncSesssion
* Converted job application example to Python
* Add LicenseServerType column to License table
* Add routes to filter by name and LicenseServerType

## 0.3.0 -- 2022-11-16
* Fixed lm-sim ip in setup scripts to use the new subapp endpoint
* Renamed script and template files to match license servers' binary filename
* Created OLicense Generator

## 0.2.0 -- 2022-08-19
* Created RLM Generator
* Created LS-Dyna Generator
* Created LM-X Generator
* Added setup scripts to copy license server binaries and fake Slurm job to cluster and add licenses to Slurm and lm-sim API
* Moved the API endpoints to a subapp in the URL http://<ip-address>:<port>/lm-sim

## 0.1.0 -- 2021-09-30
* Created CLI app to produce simulated flexlm output (from data pulled from API)
* Added fake SLURM job to credit and debit licenses
* Added unit tests
* Added FastAPI app to serve create-licenses and licenses-in-use endpoints
* Added CRUD logic over postgres database
* Created FlexLM Generator (render template with configuration values)
* Added output template (example)
* Added basic documentation (README)
