#!/bin/bash
set -e


echo "---> Installing License Manager Simulator ..."

LM_SIM_PATH="/srv/license-manager-simulator"
VENV_PIP_PATH="/srv/license-manager-agent-venv/bin/pip"
VENV_PYTHON_PATH="/srv/license-manager-agent-venv/bin/python3.12"

cp -r /app/lm_simulator $LM_SIM_PATH
find $LM_SIM_PATH -type f -name "*.py" | while read -r FILE; do
    FILE_DIR=$(dirname $FILE)

    sed -i "s|localhost|lm-simulator|gi" $FILE
    sed -i "s|/usr/bin/env python3|$VENV_PYTHON_PATH|gi" $FILE
    sed -i "s|(\".\")|(\"$FILE_DIR\")|gi" $FILE
    chmod +x $FILE
    mv $FILE ${FILE%.py}
done

$VENV_PIP_PATH install jinja2

echo " -- License Manager Simulator installed ..."
