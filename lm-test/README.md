<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/omnivector-solutions/license-manager">
    <img src="../.images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">License Manager Integration Test</h3>

  <p align="center">
    Automated integration test for License Manager Agent and API
    <br />
  </p>
</p>

# Instructions

To run the automated integration test, you'll need:

* Slurm cluster configured
* License Manager API running with the cluster already created (needs OIDC client_id)
* License Manager Simulator API running

The test should be executed in the machine where Juju is available.

It must have the `license-manager-simulator` repository cloned there.

You'll also need the `.env` file with the following values:

```bash
LM_API_BASE_URL=http://127.0.0.1:7000
LM_SIM_BASE_URL=http://127.0.0.1:7070
OIDC_DOMAIN=<your-OIDC-domain>
OIDC_CLIENT_ID=<cluster-client-id-in-OIDC>
OIDC_CLIENT_SECRET=<client-secret-to-retrieve-OIDC-token>
LM_SIM_PATH=<path-to-lm-sim-cloned-repo>
CLUSTER_ID=<cluster-id-in-lm-api>
```
