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
- [External Secrets Operator](https://external-secrets.io/) with a `ClusterSecretStore`
  (name configurable via `externalSecrets.clusterSecretStoreName`) able to back the
  `Password` generator used for DB credentials.
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
