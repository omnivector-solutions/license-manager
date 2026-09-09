# lm-api Helm Chart

Deploys the License Manager API standalone, with its own Postgres database via Kubegres
(primary/replica credentials generated through External Secrets).

Extracted from the `vantage-apis` chart in `vantage-infrastructure` (`helm/apis/templates/apis/lm`,
`helm/apis/templates/configs/lm`).

## External dependencies (not deployed by this chart)

- `ClusterSecretStore` named `k8s-secretsmanager` (External Secrets Operator), used to
  materialize generated passwords into Kubernetes Secrets.
- Kubegres operator (CRD `kubegres.reactive-tech.io/v1`).

## Install

```bash
helm install lm-api ./helm/lm-api -f my-values.yaml
```

Or straight from GHCR (see Publishing below):

```bash
helm install lm-api oci://ghcr.io/omnivector-solutions/charts/lm-api --version <chart-version>
```

See `values.yaml` for all configurable options (image, resources, ingress, AWS ECR pull
secret generation, etc).

## Publishing (CI)

- **Container image** (`.github/workflows/publish_on_tag.yaml`, job `publish-to-ghcr`):
  built from `lm-api/` and pushed to `ghcr.io/omnivector-solutions/lm-api` on every
  app version tag (same trigger/version check as the existing ECR publish job).
- **Helm chart** (`.github/workflows/publish_lm_api_helm_chart.yaml`): packaged from
  this directory and pushed as an OCI artifact to
  `oci://ghcr.io/omnivector-solutions/charts/lm-api` whenever a `lm-api-chart-v<Chart.yaml version>`
  tag is pushed (versioned independently from the app), or via manual dispatch.
  The chart's `version` in `Chart.yaml` must match the tag.

To release a new chart version: bump `version` in `Chart.yaml`, merge, then tag
`lm-api-chart-v<version>` (e.g. `lm-api-chart-v0.2.0`) and push the tag.
