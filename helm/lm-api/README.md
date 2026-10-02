# lm-api Helm Chart

Deploys the License Manager API standalone, with its own Postgres database via
[Kubegres](https://www.kubegres.io/) (primary/replica credentials generated through
[External Secrets](https://external-secrets.io/)).

This chart makes no assumptions about your cloud provider or cluster setup: it has no
hardcoded node affinity, no cloud-specific Ingress annotations, and no proprietary
add-ons. Everything infrastructure-specific (storage class, ingress class/annotations,
scheduling, image pull secrets) is left to `values.yaml` for you to fill in.

## Requirements

- A running Postgres-capable cluster with the [Kubegres operator](https://www.kubegres.io/)
  installed.
- [External Secrets Operator](https://external-secrets.io/) that serves the
  `external-secrets.io/v1` API (0.16.2 or newer, tested with 2.11.0), with a
  `ClusterSecretStore` (name configurable via `externalSecrets.clusterSecretStoreName`)
  able to back the `Password` generator used for DB credentials.
- An OIDC provider (Keycloak, Auth0, etc) to issue the JWTs lm-api validates.

## External dependencies (not deployed by this chart)

- `ClusterSecretStore` (default name `k8s-secretsmanager`, configurable) for the
  External Secrets Operator.
- Kubegres operator (CRD `kubegres.reactive-tech.io/v1`).

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
  `lm`). The same value is used for the `POSTGRES_DB` created by Kubegres and for the
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

## Postgres credentials

The primary and replica passwords are generated once by External Secrets (`Password`
generators) and stored in the `lm-kubegres-credentials` Secret. The `ExternalSecret` uses
`refreshPolicy: CreatedOnce`, so the Secret is never regenerated afterwards. This
requires an External Secrets Operator version that supports `refreshPolicy`.

The `ExternalSecret` uses `external-secrets.io/v1`. External Secrets Operator 0.17 and newer
no longer serve `v1beta1`, which older versions of this chart used.

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
