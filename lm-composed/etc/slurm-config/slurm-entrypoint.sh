#!/bin/bash
set -e


echo "---> Starting the MUNGE Authentication service (munged) ..."
chown -R munge:munge /etc/munge
chmod 700 /etc/munge
[ -f /etc/munge/munge.key ] && chmod 400 /etc/munge/munge.key
service munge start

echo "---> Starting the D-Bus system daemon (dbus) ..."
mkdir -p /run/dbus
rm -f /run/dbus/pid
dbus-daemon --system --fork

if [ "$1" = "slurmd" ]; then
    echo "---> Preparing cgroup v2 delegation for slurmd ..."
    mkdir -p /sys/fs/cgroup/init
    for p in $(cat /sys/fs/cgroup/cgroup.procs); do
        echo "$p" > /sys/fs/cgroup/init/cgroup.procs 2>/dev/null || true
    done
    echo "+cpu +cpuset +memory +io +pids" > /sys/fs/cgroup/cgroup.subtree_control
    mkdir -p "/sys/fs/cgroup/system.slice/${HOSTNAME}_slurmstepd.scope"
    echo "+cpu +cpuset +memory" > /sys/fs/cgroup/system.slice/cgroup.subtree_control
fi

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

    echo "---> Starting the Slurm Controller Daemon (slurmctld) ..."
    gosu slurm /usr/sbin/slurmctld -Dvvv &

    echo "---> Seeding the test license into Slurm ..."
    /app/seed-license-in-slurm.py

    echo "---> Configuring Prolog and Epilog scripts ..."
    /app/configure-prolog-epilog.py

    # Wait for slurmctld to finish
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
    /usr/sbin/slurmd -Dvvv &
    wait $!
    exit $?
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
