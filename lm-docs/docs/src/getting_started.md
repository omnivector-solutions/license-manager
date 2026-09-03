# Getting Started
To run License Manager you will need three different systems:

1. Slurm cluster (where the `License Manager Agent` runs on a dedicated node and the `License Manager Prolog/Epilog` scripts run on the `slurmctld` node)
2. License servers (FlexLM, RLM, LS-Dyna, LM-X, OLicense, DSLS or License Manager Simulator)
3. API with license information (`License Manager API`)

## Slurm cluster
License Manager is designed to work with Slurm. To learn how to create a Slurm cluster, please refer to the
[Omnivector Slurm Distribution documentation](https://omnivector-solutions.github.io/osd-documentation/master/index.html).

The `License Manager Agent` is decoupled from the `slurmctld` node: it can run on any dedicated node with access to the Slurm
command line tools. Only the `License Manager Prolog/Epilog` scripts need to be installed on the `slurmctld` node, where they
communicate directly with the `License Manager API` to manage bookings.

## License servers
License Manager supports the following license servers:

* FlexLM
* RLM
* LS-Dyna
* LM-X
* OLicense
* DSLS

You need to have the license server installed and working on a path that is accessible to the `License Manager Agent`.
The path for each license server binary is configurable in the `License Manager Agent` charm.
In case you don't have a license server, you can use the `License Manager Simulator` to simulate the output of a license server.

## License Manager API
The `License Manager API` is an API that stores license usage information gathered from the license servers by the agent's reconciliation
process. This data is used to update the license counters in the cluster to reflect the actual usage of the licenses.
For each license tracked by License Manager, you need to create a configuration in the API. This includes the license name, the license
features, the license server type and location, and the grace time (how long it takes for the license to be checked out after the job starts).

To learn how to set up each system needed, please refer to the [Development](development/index.md) section.
