# License-manager gen2 Design


## Goals

- license-manager is capable of tracking licenses and keeping flexlm and
  slurmdbds in sync across multiple slurm clusters.
- implementation is simplified to use a modern standard:
    - cloud runtime
    - http protocol
    - secure auth?
- [diagram][1]

[1]: https://lucid.app/lucidspark/d83d975e-9a9f-4ea6-8bfc-da9a502f7d88/edit?shared=true#


## Problem

- When a job starts, does it have the licenses it needs to run?
  - If it does not, it can start and crash, which wastes a lot of time
- Is our view of the current license counts up-to-date at the moment it's needed?
  - license users include slurm jobs, jobs from other HPC software, and jobs
    executed interactively by desktop machines.
  - slurmdbd only has a view of the license usage of slurm jobs.
  - thus, at the moment a slurm job executes, it may attempt to acquire
    licenses that are in use by non-slurm systems. If there's a mismatch, it
    will crash.
- Does our view of the current license counts include usage from other clusters?
  - Even just considering slurm jobs, there are multiple slurm clusters, each
    with its own view of license availability. Jobs from one slurm cluster may
    crash if jobs from another slurm cluster are holding licenses it needs.


## Solution

We are only attempting to solve these problems for jobs in the slurm cluster,
by having an accurate view of licenses counts from all license consumers in
the enterprise.

- When slurmdbd tries to start a job:
  1. The job runs a prolog.
  1. prolog makes an HTTP request to a service in its own cluster, the local
  agent, to confirm its license needs will be met.
  1. the agent queries flexlm (the source of truth
  for licenses).
  1. it updates another service, the backend, which is monitoring the whole
  enterprise.
  1. If there is license capacity available, the backend "books" the
  requested licenses, showing them as used.
  1. The backend responds with the number of available licenses after
  booking, or a failure response.
  1. The agent responds to the prolog with a `go` or `no-go` signal, based on
  the success of the booking.
  1. The prolog either starts the job or holds
  it, based on `go` or `no-go`.
  (Jobs that are held do not crash, so we don't have to waste time and effort
  restarting them.)


--------

## Backend

### overview

- aws lambda execution (updated by npx serverless)
  - consider using provisioned concurrency instead of a warmup function
  - if that works, we eliminate serverless completely; build a few scripts instead.
- python 3.6+ fastapi-based async service (w/ mangum adapter)
- api gateway to the world

### key components

- db postgresql (aws rds hosted)
  - python integration with sqlalchemy
  - migrations with alembic
- aws cognito for user auth
- parameter store for durable config
- terraform for cloud resource management
- getsentry/craft for releases

### configuration

- In Parameter Store
  - DATABASE_URL
    - most likely `postgresql://....`, can be sqlite for dev mode
  - ASGI_ROOT_PATH
    - this is the prefix on the URL exposing the backend, e.g. `/staging` - should match the "stage" name
  - TRUSTED_HOSTS
    - probably just `*.omnivector.solutions` and can be unset for dev mode

  - my preference would be a single toml-formatted parameter store key loaded at runtime, no environment variables.
    serverless doesn't have clean support for this though, so another reason to consider eliminating serverless

### public api

- /api
    - /v1
        - /license
            - /all (GET)
              - used/available/total token counts of all features of ALL products

            - /{product} (GET)
              - u/a/t token counts of all features of this product

            - /{product.feature} (GET)
              - u/a/t token count of this product.feature

            - /booking (PUT)
              - reserve some tokens for the listed features
              - request body structure:
                ```
                {
                  "booking": [
                      { "product_feature": "a.a", "booked": 150, },
                      { "product_feature": "a.b", "booked": 23, },
                      ...
                  ],
                  "jobid": "xxx-yyyy",   // optional
                  "comment": "whatever"  // optional
                }
                ```

                *NOTE:* these will not be stored by jobid, as this would mean bookings frequently get stranded if jobs crash and never un-book.

                *jobid* and *comment* are intended for use in log entries: after-the-fact auditing only.

            - /booking (DELETE)
              - deduct tokens for the listed features
              - same body structure as /booking (PUT), and same note re: jobid
              - counters should not go negative

            - /reconcile (PATCH)
              - update u/a/t token counts to new values.
              - request body structure:
                ```
                [
                    { "product_feature": "a.b", "booked": 11, "total": 1919 },
                    { "product_feature": "a.a", "booked": 119, "total": 1909 }
                ]
                ```
              - does not need to be a complete reconciliation of all
                features, only those listed will be updated.
            - /reconcile (PUT)  // optional, OQ
              - a PUT to this endpoint with header `X-Reconcile-Reset: true` will reset all counters

- /healthcheck (GET)
  - service status
  - software version


--------

## Cluster Agent

### Overview

- snap execution environment
- charm deployment
- python 3.6+ fastapi-based async service


### key components

- no db; agent is stateless
- no auth; agent lives inside a protected cluster
- charm for durable config?
- charm for provisioning it in the cluster
- getsentry/craft for releases (unless this is strictly coupled to backend releases)


### Public API

- supports all the GET methods (not the PUT/PATCH/DELETE methods), as these
  can simply be proxied and this would make it possible to build tools for use
  inside the cluster that display realtime counts


### Role

Polls flexlm and reconciles usage counts to the backend.

Responds to prolog requests to confirm license availability, by doing an
immediate check with flexlm and the backend.

Simplifies access to the backend API. (Only the agent has to have auth
configuration to talk to the backend.)

Simplifies configuration of the prologs which can always talk to localhost,
since the prolog and the agent are on the same physical node.
