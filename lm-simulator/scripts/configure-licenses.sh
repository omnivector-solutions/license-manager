#!/usr/bin/env bash

# Use this script to configure the simulated licenses both in the simulator API and in the Slurm cluster.
#
# This script will:
#   - Add one license for each simulated license server in the simulator API:
#       * abaqus for FlexLM;
#       * converge_super for RLM;
#       * MPPDYNA for LS-Dyna;
#       * HyperWorks for LM-X;
#       * ftire_adams for OLicense;
#   - Add the same licenses in the Slurm cluster;
#
# This script expects as argument:
#   - IP address for License Manager Simulator API
#		* format example: http://127.0.0.1:8000
#
# Note: The simulator API uses the `feature` to identify the licenses, as is done in the real license servers output.
#       The `product` is used only in the backend config row and in the Slurm cluster.
#
# After configuring the licenses, the simulated application and batch script should be seeded using the `copy-application.sh` script.

# License Manager Simulator IP address
if [ $# -eq 0 ]
    then
        echo "Please pass the simulator API IP address as an argument."
		exit
    else
        lm_sim_ip=$1
fi

# Licenses to be added to the simulator API
licenses_for_api=(
    "test_feature"
)

# Licenses to be added to the Slurm cluster
licenses_for_slurm=(
    "test_product.test_feature"
)

# Server type for Slurm licenses
server_types=(
    "flexlm"
)

# Adding licenses to License Simulator API
for license in ${licenses_for_api[@]}; do
    echo "Adding $license license to simulator API"
    data='{"name": "'
    data+="$license"
    data+='", "total": 1000}'

    curl --request POST \
    --url $lm_sim_ip/lm-sim/licenses/ \
    --header 'Content-Type: application/json' \
    --data "$data"
done

# Adding licenses to Slurm cluster
for i in {0..4}; do
    echo "Adding ${licenses_for_slurm[$i]} license to Slurm cluster"
    juju ssh slurmctld/leader sudo sacctmgr add resource Type=license Clusters=osd-cluster \
        Server=${server_types[$i]} Names=${licenses_for_slurm[$i]} Count=1000 ServerType=${server_types[$i]} PercentAllowed=100 -i
done

echo "Licenses configured!"