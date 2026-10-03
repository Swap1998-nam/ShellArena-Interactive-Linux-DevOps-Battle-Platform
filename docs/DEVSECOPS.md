# DevSecOps implementation

The pipeline files are ready to configure in your environment. No hosted CI run, registry push, SonarQube server analysis, container image scan, or Kubernetes rollout was performed from this workspace.

## GitHub Actions

`.github/workflows/ci.yml` runs on pull requests, main/master pushes, feature branches, and manual dispatch. Actions are pinned to verified full commit SHAs. Workflow token permissions are read-only.

- Ruff and JavaScript syntax checks.
- Pytest API/security suite with an 88% coverage floor.
- Bandit medium/high checks and pip-audit for the pinned runtime dependency set.
- Browser workflow tests in Chromium, including mobile layouts and escaped terminal output.
- Container build followed by Trivy filesystem secret/misconfiguration scanning and a high/critical vulnerability gate.
- CycloneDX image SBOM and quality artifacts.

A failed scanner gate fails the job. There is no blanket vulnerability allowlist or `continue-on-error`. Review and fix findings as the advisory database changes; a clean scan today does not imply future clean scans.

Protect the default branch and require the `quality` and `container-security` checks before merging. Dependency update proposals are configured in `.github/dependabot.yml`. Review their diffs and rerun checks.

## Jenkins

Create a Pipeline from SCM pointing to the repository and its `Jenkinsfile`. Use a dedicated trusted agent labelled `docker` with:

- Python 3.12 and venv support.
- Node.js 20+ and npm.
- Docker CLI/daemon appropriate for trusted builds.
- Trivy installed from its official distribution, with its version managed by your agent image.
- Chromium runtime libraries for Playwright (`npx playwright install --with-deps chromium` while provisioning the agent).
- Git and optional SonarScanner/Jenkins SonarQube integration.

Stages: checkout → install/lint → tests → security gates → browser workflows → optional Sonar analysis/quality gate → build/scan/SBOM → optional registry push.

`PUBLISH_IMAGE` defaults to false. Configure `REGISTRY` and `IMAGE_REPOSITORY`, then create the Jenkins username/password credential `container-registry` with a narrowly scoped registry token. Enable publishing only for trusted release jobs. Never run untrusted PR code on an agent with production secrets or a privileged Docker daemon.

Images use `build-BUILD_NUMBER`, not `latest`. Record the registry digest after push and use that digest for deployment. Deployment is a separate step; the Jenkinsfile does not automatically modify your cluster.

## SonarQube

1. In Jenkins, configure the SonarQube server with the exact name `SonarQube`; store its token in Jenkins credentials.
2. Add a scanner tool named `SonarScanner` and install the SonarQube Scanner plugin.
3. Create the ShellArena project, with key `shellarena`.
4. Configure the SonarQube webhook to `https://YOUR_JENKINS/sonarqube-webhook/` so `waitForQualityGate` can complete. Protect and validate this integration for your installation.
5. Set the project's quality gate; enable `RUN_SONAR` in Jenkins.

`sonar-project.properties` maps Python coverage from `coverage.xml` and scans backend/frontend source. The pipeline waits for the quality gate and aborts if it fails. When the parameter is off, no Sonar analysis is claimed.

## Local gates

```bash
make lint
make test
make security
npm ci --ignore-scripts
npx playwright install --with-deps chromium
npm run test:browser

docker build --pull -t shellarena:review .
trivy fs --scanners misconfig,secret --severity HIGH,CRITICAL --exit-code 1 .
trivy image --severity HIGH,CRITICAL --exit-code 1 shellarena:review
trivy image --format cyclonedx --output sbom.cdx.json shellarena:review
```

## Before a wider public launch

Run the actual image/cluster gates, restore a backup into staging, load-test authenticated commands, set resource/retention limits, configure trusted gateway rate limiting, establish account recovery/data deletion procedures, and have the deployed system independently reviewed. Real multi-tenant shell execution and highly available storage are separate engineering projects.
