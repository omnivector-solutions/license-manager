#!/bin/bash
set -e


ACCOUNT_NAME="license-manager"
USER_NAME="license-manager"
PARTITION_NAME="example_partition"
OPERATOR_LEVEL="Operator"

# Configure License Manager Slurm account
sacctmgr add account $ACCOUNT_NAME Description=License Manager reservations account -i

# Setup License Manager user
sacctmgr add user $USER_NAME account=$ACCOUNT_NAME AdminLevel=Operator -i

# Create Abaqus license
sacctmgr add resource Type=license Clusters=linux Server=flexlm Names=abaqus.abaqus Count=1000 ServerType=flexlm PercentAllowed=100 -i
