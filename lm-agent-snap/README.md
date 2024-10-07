# lm-agent-snap
The License Managar Agent bundled into a Snap.

# Installation instructions

For installing from the Snap Store, run:
```bash
sudo snap install license-manager-agent
```

## Basic Usage

This snap requires a few configuration values to be set before it can be used. The required values are:
- oidc-client-id: The client ID of the OIDC application that the agent will use for authentication.

- oidc-client-secret: The client secret of the OIDC application that the agent will use for authentication.

The optional values are:
- backend-base-url: The URL of the License Manager API server where the agent will send its data. Setting/unsetting this value is more interesting when using the snap in a development environment; do not change it otherwise.

- oidc-domain: The domain of the OIDC server that the agent will use for authentication. Setting/unsetting this value is more interesting when using the snap in a development environment; do not change it otherwise.

- sacctmgr-path: The absolute path to the *sacctmgr* command on the host system. This is optional and defaults to /usr/bin/sacctmgr.

- scontrol-path: The absolute path to the *scontrol* command on the host system. This is optional and defaults to /usr/bin/scontrol.

- squeue-path: The absolute path to the *squeue* command on the host system. This is optional and defaults to /usr/bin/squeue.

- lmutil-path: Absolute path to the binary for lmutil (needed for FlexLM licenses). Defaults to /usr/local/bin/lmutil.

- rlmutil-path: Absolute path to the binary for rlmutil (needed for RLM licenses). Defaults to /usr/local/bin/rlmutil.

- lsdyna-path: Absolute path to the binary for lstc_qrun (needed for LS-Dyna licenses). Defaults to /usr/local/bin/lsdyna.

- lmxendutil-path: Absolute path to the binary for lmxendutil (needed for LM-X licenses). Defaults to /usr/local/bin/lmxendutil.

- olixtool-path: Absolute path to the binary for olixtool (needed for OLicense licenses). Defaults to /usr/local/bin/olixtool.

- reservation-identifier: Reservation name used when doing the reconciliation. Defaults to *license-manager-reservation*.

- lm_user: System user name used when creating reservations. Defaults to *license-manager*.

- stat-interval: Interval in seconds used to report the cluster status to the API. Defaults to 60.

- tool-timeout: Timeout in seconds for the license server binaries. Defaults to 6.

- encoding: Encoding used for decoding the output of the license server binaries. Defaults to *utf-8*.

Any configuration can be set using the *snap* command line, e.g.:
```bash
sudo snap set license-manager-agent oidc-client-id=foo
sudo snap set license-manager-agent oidc-client-secret=boo
```

# Development

For development purposes, you can build the `license-manager-agent` part prior to packing the snap. To do that, run:
```bash
snapcraft prime -v
```

Add the `--debug` flag for creating a shell in case there's any error after the build is complete.

For building the snap end-to-end, run:
```bash
snapcraft -v --debug
```

Once the command completes successfully, a `.snap` file will be created in the directory. For installing this snap, run:
```bash
sudo snap install --dangerous license-manager-agent_<snap version>_amd64.snap
```

Once the snap is installed, it is possible to check the status of the daemon and the logs:
```bash
systemctl status snap.license-manager-agent.daemon  # check the daemon status
sudo journalctl -u snap.license-manager-agent.daemon --follow  # follow the agent logs
```

Sometimes is important to clean the environment for deleting cached files and dependencies. For doing that, run:
```bash
sudo snapcraft clean
```

# Publish

Every time a new tag is created, a new version of the snap will be published to the *latest/candidate* and *latest/edge* channels. The version follows the pattern `<snap version>-<git revision>`, e.g. `1.0.0-8418de0`.