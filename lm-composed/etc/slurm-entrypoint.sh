#!/bin/bash
set -e


echo "---> Starting the MUNGE Authentication service (munged) ..."
service munge start

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

    exec gosu slurm /usr/sbin/slurmdbd -Dvvv
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

    echo "---> Installing lm-agent ..."
    cd /app/lm-agent
    poetry install

    echo "---> Installing lm-simulator ..."
    poetry add /app/lm-simulator
    
    echo "---> Polutating LM API with pre-defined license ..."
    /app/populate-lm-api.py

    echo "---> Polutating LM Simulator API with pre-defined license ..."
    /app/populate-lm-simulator-api.py

    echo "---> Starting the License Manager Agent (lm-agent) ..."
    poetry run license-manager-agent &

    echo "---> Starting the Slurm Controller Daemon (slurmctld) ..."
    gosu slurm /usr/sbin/slurmctld -Dvvv &

    echo "---> Seeding the test license into Slurm ..."
    /app/seed-license-in-slurm.py

    echo "---> Configuring Prolog and Epilog scripts ..."
    /app/configure-prolog-epilog.py

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
    exec /usr/sbin/slurmd -Dvvv
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
    exec /usr/sbin/slurmrestd -vvvv -a rest_auth/jwt 0.0.0.0:6820
fi

exec "$@"
