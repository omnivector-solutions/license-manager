# lm-api Helm Chart

Deploys the License Manager API standalone, with its own Postgres database via
[CloudNativePG](https://cloudnative-pg.io/). CloudNativePG generates and stores its own
app credentials; optional continuous backup to S3 is available via `postgres.backup.*`.

This chart makes no assumptions about your cloud provider or cluster setup: it has no
hardcoded node affinity, no cloud-specific Ingress annotations, and no proprietary
add-ons. Everything infrastructure-specific (storage class, ingress class/annotations,
scheduling, image pull secrets) is left to `values.yaml` for you to fill in.

## Requirements

- A cluster with the [CloudNativePG operator](https://cloudnative-pg.io/) installed
  (CRD `postgresql.cnpg.io/v1`).
- An OIDC provider (Keycloak, Auth0, etc) to issue the JWTs lm-api validates.

## External dependencies (not deployed by this chart)

- CloudNativePG operator (CRD `postgresql.cnpg.io/v1`).

## Install

```bash
helm install lm-api ./helm/lm-api -f my-values.yaml
```

Or straight from GHCR (see Publishing below):

```bash
helm install lm-api oci://ghcr.io/omnivector-solutions/charts/lm-api --version <chart-version>
```

At minimum, set `auth.armasecDomain` to your OIDC realm (e.g.
`keycloak.example.com/realms/license-manager`).

See `values.yaml` for all configurable options: image, resources, scheduling
(`affinity`/`tolerations`/`nodeSelector`), autoscaling, ingress, Sentry, storage class.

## Multi-tenancy

Multi-tenancy is **disabled by default** (`multiTenancy.enabled: false`).

- **Disabled:** lm-api uses a single database, named by `postgres.database` (default
  `lm`). The same value is used for the database CloudNativePG bootstraps and for the
  `DATABASE_NAME` passed to the API, so they always match.
- **Enabled:** lm-api selects the database per request from the organization id in the
  user's token, and `DATABASE_NAME` is not set. Tenant databases must already exist,
  named after the organization id (UUID).

```yaml
multiTenancy:
  enabled: true
```

Upgrading from chart `0.1.x`: the old chart hardcoded `MULTI_TENANCY_ENABLED=true`. Set
`multiTenancy.enabled: true` to keep that behavior.

## Database migrations

An init container (`migration`) runs `alembic upgrade head` before the API starts, after
the `pgchecker` init container confirms Postgres is reachable. The script is shipped in
the `lm-check-migration` ConfigMap.

- Multi-tenancy disabled: migrates the `postgres.database` database.
- Multi-tenancy enabled: migrates every database whose name is a UUID.

The lm-api image does not include alembic, so the init container installs it at startup
with `pip` (version set by `migration.alembicVersion`). The cluster needs egress access to
a PyPI index for the pod to start.

## Postgres

CloudNativePG creates the `lm-postgres` Cluster and a `lm-postgres-app` Secret holding
the generated `username`/`password` for the database owner (`postgres.owner`, default
`lm`); the API and the migration job read their credentials from that Secret.
`postgres.highAvailability: true` (default) runs 2 instances (1 primary + 1 standby)
with pod anti-affinity; set it to `false` for a single instance.

Continuous backup is **disabled by default**. Set `postgres.backup.enabled: true` and
provide a bucket plus credentials (`postgres.backup.destinationPath`,
`accessKeyId`/`secretAccessKey` or `existingSecret`) to enable it; this chart does not
provision the bucket itself. It uses CloudNativePG's native Barman Cloud integration,
which upstream has deprecated in favor of the separate Barman Cloud Plugin (removal
planned for CloudNativePG 1.28); this chart will move to the plugin before that happens.

## Publishing (CI)

- **Container image** (`.github/workflows/publish_on_tag.yaml`, job `publish-to-ecr`):
  built from `lm-api/` and pushed to both Amazon ECR and
  `ghcr.io/omnivector-solutions/lm-api` (tags: app version + `latest`) on every app
  version tag. The GHCR image carries `org.opencontainers.image.source/version/revision`
  labels so it shows up linked to this repository and version on GHCR.
- **Helm chart** (`.github/workflows/publish_lm_api_helm_chart.yaml`): packaged from
  this directory and pushed as an OCI artifact to
  `oci://ghcr.io/omnivector-solutions/charts/lm-api` whenever a
  `lm-api-chart-v<Chart.yaml version>` tag is pushed (versioned independently from the
  app), or via manual dispatch. The chart's `version` in `Chart.yaml` must match the tag.

To release a new chart version: bump `version` in `Chart.yaml`, merge, then tag
`lm-api-chart-v<version>` (e.g. `lm-api-chart-v0.2.0`) and push the tag.
