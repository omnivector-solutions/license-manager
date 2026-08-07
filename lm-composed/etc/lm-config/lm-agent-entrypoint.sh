#!/bin/bash
set -e

echo "---> Starting the MUNGE Authentication service (munged) ..."
mkdir -p /var/log/munge /var/lib/munge /run/munge /etc/munge
if [ ! -f /etc/munge/munge.key ]; then
    dd if=/dev/urandom of=/etc/munge/munge.key bs=1 count=1024
fi
chown -R munge:munge /etc/munge /var/log/munge /var/lib/munge /run/munge
chmod 700 /etc/munge
chmod 400 /etc/munge/munge.key
runuser -u munge -- /usr/sbin/munged

cd /app/lm-agent

echo "---> Installing lm-agent and lm-simulator into the shared venv ..."
uv sync --inexact
uv pip install /app/lm-simulator

echo "---> Populating LM API with pre-defined license ..."
uv run /app/populate-lm-api.py

echo "---> Populating LM Simulator API with pre-defined license ..."
uv run /app/populate-lm-simulator-api.py

echo "---> Starting the License Manager Agent (lm-agent) ..."
exec uv run license-manager-agent
