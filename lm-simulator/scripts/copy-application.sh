#!/usr/bin/env bash

# Use this script to copy the simulated application to the slurmd node.
#
# This script will:
#   - Copy application and batch scripts to the slurmd node;
#   - Configure the Slurm partition to match the one defined in the batch file;
#
# This script expects as argument:
#   - IP address for License Manager Simulator API
#		* format example: http://127.0.0.1:8000
#
# Note: To run the application you need to specify which license will be used in both the application and batch script files.
#       For simplicity, this script will change the files to use 42 `abaqus` licenses.
#       If you need to test other license servers, change the license to the equivalent for the license server you need.

# License Manager Simulator IP address
if [ $# -eq 0 ]
    then
        echo "Please pass the simulator API IP address as an argument."
		exit
    else
        lm_sim_ip=$1
fi

# Change ip address in application file
echo "Updating application file with simulator ip address"
sed -i "s|http://localhost:8000|$lm_sim_ip|gi" ./job/application.sh

# Copy batch and application files to slurmd node
echo "Copying files to slurmd node"
juju scp ./job/batch.sh slurmd/leader:/tmp
juju scp ./job/application.sh slurmd/leader:/tmp

# Config Slurm partition
echo "Configuring Slurm partition as mypartition"
juju config slurmd partition-name=mypartition

echo "Application and batch script copied to slurmd!"
