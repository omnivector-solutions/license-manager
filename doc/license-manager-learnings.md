# License Manager learnings

1. what are the products that are licensed, require a license?

    - there are no licenses to run slurm itself, but slurm is doing some work to track them
    - hpc applications (sample)
        - abaqus (commercial, HAS licenses, has features)
        - openfoam (open source, no licenses)
        - solidworks (commercial, user-interactive gui that uses the hpc backend, HAS licenses, also has gui license (don't care))
        - catia (commercial, like solidworks, HAS licenses, also has gui license (don't care))
        - matlab (commercial, HAS licenses, has features, like abaqus)

2. slurm, slurmdbd, flexlm

    - slurmdbd: cluster info, job info
        - TBD: schema
        - has a counter for abaqus licenses, and checks if there are enough free before starting the next job
        - `sacctmgr modify resource name={feature} set count={tokens} -i` to tell slurm how many licenses

    - abaqus talks to flexlm to reserve and free licenses

    - workflow
        - slurm checks slurmdbd for sufficient licenses before starting the job
        - after it starts, even though slurmdbd says there are sufficient tokens, the
          job can fail when abaqus can't get free tokens from flexlm
        - after it ends, abaqus returns tokens to flexlm, but it can also crash (tokens are unreturned)

3. license-manager problem being solved

    - queue:
        - job1 (needs 500 abaqus.abaqus tokens) - 5 minutes setup
        - job2 (500) - 5 minutes setup
        - job3 (500) - no setup

    - slurm will not let you schedule a job if you are requesting more licenses than available
    - will slurm run a queued job iif there aren't licenses available?
        - no. slurm is aware that you don't have enough licenses and will hold the queue item until
          there are enough free.

4. lm runtimes, examples (all from scania env):
    - first log in: `juju switch JBEMFV@scania/penny-november-staging; juju ssh cdxfdn@login/0`
    - (you can log in as ubuntu@login/0 to install any sw you need, with `yum`)
    - catia: /doc/example/catia.txt
    - rlm(?): /doc/example/rlm.txt - errors here
    - lmx(?): /doc/example/lmx.txt - errors here
    - lstc(?): /doc/example/lstc.txt - segv here!

## Glossary?
- "license features"
- "abaqus license with the abaqus feature" (tokens)
    e.g. abaqus.gpu=500
    e.g. abaqus.abaqus=1000
    (50-100 other features of abaqus)
- `lmutil` -> flexlm tool
