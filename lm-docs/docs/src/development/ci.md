# Continuous Integration

License Manager employs [GitHub Actions](https://github.com/omnivector-solutions/license-manager/actions)
for its continuous integration processes. Detailed descriptions of these actions are
provided on this page.

## Automated Quality Assurance

The
[test_on_push.yaml](https://github.com/omnivector-solutions/license-manager/blob/main/.github/workflows/test_on_push.yaml)
action runs the quality assurance checks (`make qa`: unit tests, linters, formatters,
type checkers) for each sub-project (`lm-agent`, `lm-api`, `lm-cli`, `lm-simulator`,
`lm-simulator-api`) independently. It is triggered on every push to `main`/`release/**`
and on every pull request.

## Automated Publication

License Manager's sub-projects are published to PyPI, the API and CLI container
images are published to Amazon ECR and [GHCR](https://ghcr.io/omnivector-solutions),
the standalone Helm chart is published to GHCR as an OCI artifact, and the agent snap
is released to the Snap Store's edge/candidate channels. These are handled by three
linked GitHub Actions, detailed below.

### Prepare for release

[prepare_release.yaml](https://github.com/omnivector-solutions/license-manager/blob/main/.github/workflows/prepare_release.yaml)
is triggered manually via a workflow dispatch whenever new features or fixes need to
be published. It takes a base version bump (`major`/`minor`/`patch`/`stable`) and an
optional prerelease/stage bump (`alpha`/`beta`/`rc`/`post`/`dev`) as inputs.

Once activated, this action:

- Uses `uv` to bump the version on all five sub-projects (`lm-agent`, `lm-api`,
  `lm-cli`, `lm-simulator`, `lm-simulator-api`) to the same new version, and fails if
  they end up out of sync.
- Builds the changelog for the new version with Towncrier.
- Creates a new branch named `prepare-release/<version>`.
- Opens a draft pull request titled `Release <version>`.

This lets all the changes above be reviewed, with the full QA suite running against
the pull request, before anything is published.

### Create a new tag

[tag_on_merged_pull_request.yaml](https://github.com/omnivector-solutions/license-manager/blob/main/.github/workflows/tag_on_merged_pull_request.yaml)
triggers once the release PR (branch `prepare-release/<version>`) is merged into
`main` or a `release/**` branch. It creates and pushes a new git tag named after the
version.

### Publish on Tag

[publish_on_tag.yaml](https://github.com/omnivector-solutions/license-manager/blob/main/.github/workflows/publish_on_tag.yaml)
triggers when a version tag is pushed. It double-checks the tag matches each
sub-project's version, then:

- Builds and publishes `lm-agent`, `lm-api`, `lm-cli`, `lm-simulator` and
  `lm-simulator-api` to PyPI.
- Builds a single Docker image from `lm-api/` and pushes it to both Amazon ECR
  (Vantage's private registry) and [GHCR](https://ghcr.io/omnivector-solutions/lm-api),
  publicly, tagged with both the version and `latest`. The GHCR image carries
  `org.opencontainers.image.source`, `.version` and `.revision` OCI labels, so it
  shows up on GHCR linked back to this repository and to the exact tag it was built
  from.
- Builds the `lm-agent` snap and releases it to the Snap Store's `edge`/`candidate`
  channels.

## Automated Publication of the Helm Chart

lm-api can also be deployed standalone via the Helm chart at
[`helm/lm-api`](https://github.com/omnivector-solutions/license-manager/tree/main/helm/lm-api)
in this repository. It is a generic chart with no cloud-specific assumptions (no
hardcoded node affinity, no cloud Ingress annotations); see the chart's own
`README.md` for requirements and configuration.

The chart is versioned independently from the application (its own `version` in
`Chart.yaml`), since chart changes (e.g. a resource limit tweak) happen at a very
different cadence than application releases. It is published by
[publish_lm_api_helm_chart.yaml](https://github.com/omnivector-solutions/license-manager/blob/main/.github/workflows/publish_lm_api_helm_chart.yaml),
which:

- Triggers on its own tag, `lm-api-chart-v<Chart.yaml version>` (e.g.
  `lm-api-chart-v0.2.0`), or via manual workflow dispatch.
- Fails if the tag doesn't match the chart's `version` in `Chart.yaml`.
- Packages the chart and pushes it as an OCI artifact to
  `oci://ghcr.io/omnivector-solutions/charts/lm-api`.
- Attaches the packaged `.tgz` to a GitHub Release for that tag.

To release a new chart version: bump `version` in `helm/lm-api/Chart.yaml`, merge to
`main`, then tag and push `lm-api-chart-v<version>`.

Install directly from GHCR with:

```bash
helm install lm-api oci://ghcr.io/omnivector-solutions/charts/lm-api --version <chart-version>
```
