#!/usr/bin/env bash

# Use this script to configure a working license-manager-agent deployed charm to use the license-manager-simulator.
#
# This script will:
#	- Copy script and template for simulating each supported license server in the agent machine;
#	- Rename and move those files to their correct location;
#   - Set the binaries' location in the charm via juju config;
#	- Install jinja2 in the agent's venv to render the templates;
#	- Start the agent service in the agent machine;
#
# This script expects as argument:
#   - IP address for License Manager Simulator API
#		* format example: http://127.0.0.1:8000
#
# After preparing the environment, the licenses should be configured using the `configure-licenses.sh` script.

# License Manager Simulator IP address
if [ $# -eq 0 ]
    then
        echo "Please pass the simulator API IP address as an argument."
		exit
    else
        lm_sim_ip=$1
fi

# Python executable path
python_path="#!/srv/license-manager-agent-venv/bin/python3.8"
# Path where the templates and scripts will be copied to
file_path="/srv/license-manager-agent-venv/lib/python3.8/site-packages/bin"

# Folder names (one for each license server supported)
folders=(
	"flexlm"
	"rlm"
	"lsdyna"
	"lmx"
	"olicense"
)

# Scripts that will be copied to the machine
scripts=(
	"lmutil.py"
	"rlmutil.py"
	"lstc_qrun.py"
	"lmxendutil.py"
	"olixtool.py"
)

# License server binary names (will be simulated using the scripts)
binary_names=(
	"lmutil"
	"rlmutil"
	"lstc_qrun"
	"lmxendutil"
	"olixtool.py"
)

# Template files that will render information retrieved from the simulator backend
templates=(
	"lmutil.out.tmpl"
	"rlmutil.out.tmpl"
	"lstc_qrun.out.tmpl"
	"lmxendutil.out.tmpl"
	"olixtool.out.tmpl"
)

# Charm configs that indicate where each binary is located 
configs=(
	"lmutil-path"
	"rlmutil-path"
	"lsdyna-path"
	"lmxendutil-path"
	"olixtool-path"
)

# Changing path and ip address in script files
for i in {0..4}; do
	echo "Updating ${folders[$i]}/${scripts[$i]} file"
	sed -i "s|#!/usr/bin/env python3|$python_path|gi" ./bin/${folders[$i]}/${scripts[$i]}
	sed -i "s|(\".\")|(\"$file_path\")|gi" ./bin/${folders[$i]}/${scripts[$i]}
	sed -i "s|http://localhost:8000|$lm_sim_ip|gi" ./bin/${folders[$i]}/${scripts[$i]}
done

# Copying script and template files to machine
juju ssh license-manager-agent/leader mkdir /tmp/simulator-files

for folder in ${folders[@]}; do
	echo "Copying files from $folder to license-manager-agent machine"
	juju scp -- -r ./bin/$folder license-manager-agent/leader:/tmp/simulator-files
done

# Creating bin folder
juju ssh license-manager-agent/leader sudo mkdir $file_path

# Moving files to correct location and adding executable permission
for i in {0..4}; do
	echo "Moving ${scripts[$i]} script file and renaming to ${binary_names[$i]}"
	juju ssh license-manager-agent/leader sudo mv /tmp/simulator-files/${folders[$i]}/${scripts[$i]} $file_path/${binary_names[$i]}

	echo "Adding executable permission to ${binary_names[$i]} file"
	juju ssh license-manager-agent/leader sudo chmod +x $file_path/${binary_names[$i]}

	echo "Moving template ${templates[$i]}"
	juju ssh license-manager-agent/leader sudo mv /tmp/simulator-files/${folders[$i]}/${templates[$i]} $file_path
done

# Configuring binaries' path in the charm to the correct location
for i in {0..4}; do
	echo "Setting ${configs[$i]} charm config"
	juju config license-manager-agent ${configs[$i]}=$file_path/${binary_names[$i]}
done

# Installing Jinja2 to agent venv to render templates
echo "Installing Jinja2 in the agent's venv"
juju scp ./scripts/install-jinja2.sh license-manager-agent/leader:/tmp/simulator-files
juju ssh license-manager-agent/leader sudo chmod +x /tmp/simulator-files/install-jinja2.sh
juju ssh license-manager-agent/leader /tmp/simulator-files/install-jinja2.sh

# Deleting temporary folders
echo "Deleting temporary simulator files"
juju ssh license-manager-agent/leader rm -rf /tmp/simulator-files

# Starting the agent service
echo "Starting license-manager-agent service"
juju ssh license-manager-agent/leader sudo systemctl daemon-reload
juju ssh license-manager-agent/leader sudo systemctl start license-manager-agent.timer
juju ssh license-manager-agent/leader sudo systemctl start license-manager-agent.service

echo "Environment configured!"