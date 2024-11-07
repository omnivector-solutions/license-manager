#!/app/lm-agent/.venv/bin/python
import os
import re
import subprocess


ENV_FILE = "/etc/default/license-manager-agent"

env_vars = os.environ.items()

with open(ENV_FILE, "w") as file:
    for key, value in env_vars:
        file.write(f"export {key}={value}\n")


SLURM_CONF_PATH = "/etc/slurm/slurm.conf"
PROLOG_PATH = "/app/slurmctld_prolog.sh"
EPILOG_PATH = "/app/slurmctld_epilog.sh"


with open(SLURM_CONF_PATH, "r") as file:
    content = file.read()

content = re.sub(r"^#PrologSlurmctld=.*", f"PrologSlurmctld={PROLOG_PATH}", content, flags=re.MULTILINE)
content = re.sub(r"^#EpilogSlurmctld=.*", f"EpilogSlurmctld={EPILOG_PATH}", content, flags=re.MULTILINE)

with open(SLURM_CONF_PATH, "w") as file:
    file.write(content)

output_pkill = subprocess.run(["pkill", "-SIGTERM", "-f", "slurmctld"])
if output_pkill.returncode != 0:
    print(f"Failed to kill slurmctld, return code: {output_pkill.returncode}")
    exit(1)

output_gosu = subprocess.run(["gosu", "slurm", "/usr/sbin/slurmctld", "-Dvvv", "&"])
if output_gosu.returncode != 0:
    print(f"Failed to start slurmctld, return code: {output_gosu.returncode}")
    exit(1)
