# Change Log

This file keeps track of all notable changes to license-manager-simulator

## Unreleased
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
