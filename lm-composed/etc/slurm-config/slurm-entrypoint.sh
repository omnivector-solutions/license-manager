#!/bin/bash
set -e

# Set library path for Slurm shared libraries
export LD_LIBRARY_PATH="/opt/slurm/view/lib/private:/opt/slurm/view/lib:/opt/slurm/view/lib/slurm:${LD_LIBRARY_PATH}"

if [ "$1" = "slurmdbd" ]
then
    echo "---> Starting the Slurm Database Daemon (slurmdbd) ..."
    {
        . /etc/slurm/slurmdbd.conf
        until echo "SELECT 1" | mysql -h $StorageHost -u$StorageUser -p$StoragePass 2>&1 > /dev/null
        do
            echo "-- Waiting for database to become active ..."
            sleep 2
        done
    }
    echo "-- Database is now active ..."

    exec gosu slurm /opt/slurm/view/sbin/slurmdbd -Dvvv
fi

if [ "$1" = "slurmctld" ]
then
    echo "---> Waiting for slurmdbd to become active before starting slurmctld ..."

    until 2>/dev/null >/dev/tcp/slurmdbd/6819
    do
        echo "-- slurmdbd is not available.  Sleeping ..."
        sleep 2
    done
    echo "-- slurmdbd is now active ..."


    echo "---> Starting the Slurm Controller Daemon (slurmctld) ..."
    gosu slurm /opt/slurm/view/sbin/slurmctld -Dvvv &

    # Sleep to allow slurmctld to start
    sleep 3

    # Define environment for Python scripts that need Slurm commands
    SLURM_ENV="PATH=/opt/slurm/view/bin:/opt/slurm/view/sbin:/usr/local/bin:/usr/bin:/bin LD_LIBRARY_PATH=/opt/slurm/view/lib/private:/opt/slurm/view/lib:/opt/slurm/view/lib/slurm HOME=/root"

    echo "---> Seeding the test license into Slurm ..."
    env -i $SLURM_ENV /usr/bin/python3 /app/seed-license-in-slurm.py

    echo "---> Configuring Prolog and Epilog scripts ..."
    env -i $SLURM_ENV /usr/bin/python3 /app/configure-prolog-epilog.py

    # Wait for both slurmctld and lm-agent to finish
    wait -n
fi

if [ "$1" = "slurmd" ]
then
    echo "---> Waiting for slurmctld to become active before starting slurmd..."

    until 2>/dev/null >/dev/tcp/slurmctld/6817
    do
        echo "-- slurmctld is not available.  Sleeping ..."
        sleep 2
    done
    echo "-- slurmctld is now active ..."

    echo "---> Starting the Slurm Node Daemon (slurmd) ..."
    exec /opt/slurm/view/sbin/slurmd -Dvvv
fi

if [ "$1" = "slurmrestd" ]
then

    echo "---> Waiting for slurmctld to become active before starting slurmrestd..."

    until 2>/dev/null >/dev/tcp/slurmctld/6817
    do
        echo "-- slurmctld is not available.  Sleeping ..."
        sleep 2
    done
    echo "-- slurmctld is now active ..."

    echo "---> Starting the Slurm Rest API (slurmrestd) ..."
    exec /opt/slurm/view/sbin/slurmrestd -vvvv -a rest_auth/jwt 0.0.0.0:6820
fi

exec "$@"
