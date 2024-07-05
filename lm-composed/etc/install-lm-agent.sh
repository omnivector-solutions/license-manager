#!/bin/bash
set -e
   

echo "---> Installing License Manager Agent ..."

PYTHON_PATH="/opt/python/python3.12/bin/python3.12"
VENV_PATH="/srv/license-manager-agent-venv"
VENV_PIP_PATH="/srv/license-manager-agent-venv/bin/pip"
VENV_PYTHON_PATH="/srv/license-manager-agent-venv/bin/python3.12"

# Install lm-agent from mounted volume
$PYTHON_PATH -m venv $VENV_PATH
$VENV_PIP_PATH install --upgrade pip
$VENV_PIP_PATH install /app

echo " -- License Manager Agent installed ..."
