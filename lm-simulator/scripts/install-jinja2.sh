#!/usr/bin/env bash

# Use this script to install Jinja2 in the license-manager-agent venv to render templates.
#
# This script will:
#   - Log in as root;
#   - Activate the venv;
#	- Install the package inside the venv;
#
# Note: It needs to be run as root, otherwise the installation will fail.

# Activate venv as root and install jinja2 package
sudo -i -u root bash << EOF
source /srv/license-manager-agent-venv/bin/activate
pip install jinja2
EOF

echo "Jinja2 installed on agent venv!"