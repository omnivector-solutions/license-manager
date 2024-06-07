#!/usr/bin/env bash

# Use this script to create a development setup for License Manager Simulator.
#
# This script will:
#   - Read the IP address for License Manager Simulator API;
#   - Execute all scripts, passing the IP to them:
#       * prepare-environment.sh: copy scripts and templates to agent machine;
#       * configure-licenses.sh: create licenses in the API and in Slurm;
#       * copy-application.sh: copy fake application and batch script to slurmd machine;
#
# This script expects as argument:
#   - IP address for License Manager Simulator API
#		* format example: http://127.0.0.1:8000
#
# To run this script you need to have the simulator API running. Use `docker-compose up` to run the API.

# License Manager Simulator IP address
if [ $# -eq 0 ]
    then
        echo "Please pass the simulator API IP address as an argument."
        exit
    else
        lm_sim_ip=$1
fi

# Scripts to be run
scripts=(
    "prepare-environment.sh"
    "configure-licenses.sh"
    "copy-application.sh"
)

# Running scripts
for script in ${scripts[@]}; do
    echo "Executing script: $script"
    ./scripts/$script $lm_sim_ip
done

echo "All done!"