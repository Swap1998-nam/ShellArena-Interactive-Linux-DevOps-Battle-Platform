# Validation record — 2026-09-27

Base repository commit: `dfbbd4f`.
Working branch: `feat/shellarena-production-foundation`.

## Executed successfully

| Check | Observed result |
| --- | --- |
| Pytest | 50 tests passed |
| Backend coverage | Approximately 94% overall; includes the unexecuted optional Docker helper in the denominator |
| Mission completion | All 16 missions completed through API tests; replay XP remained zero |
| Concurrent completion | Four concurrent finish requests awarded XP exactly once |
| Ownership/security | Foreign-lab access rejected; CSRF, cross-site requests, input limits, host-file isolation, cookie revocation tested |
| Persistence | Account upgrade, login, and application restart preserve progress |
| Browser workflows | 10 checks passed against a real two-worker Gunicorn server with a temporary database |
| Responsive checks | Desktop 1440px and mobile 390px rendered without horizontal overflow; screenshots visually reviewed |
| Browser safety | Terminal HTML displayed as text; no uncaught page errors or CSP violations in tested workflows |
| Python lint | Ruff passed |
| JavaScript parse | `node --check frontend/app.js` passed |
| Source security scan | Bandit medium/high gate passed; narrow virtual-path/container-mount exceptions documented |
| Runtime dependency audit | pip-audit reported no known vulnerabilities in the pinned runtime requirements at check time |
| WSGI config | Gunicorn configuration check passed |
| Configuration syntax | Compose, Kubernetes, monitoring, and GitHub YAML parsed successfully; Grafana JSON parsed successfully |

The browser checks cover navigation, search/category/difficulty filtering, bookmarking, objective completion, refreshed history, escaped output, guest-account upgrade, privacy settings, leaderboard opt-in, sign-out/sign-in, hints, workspace restart, and mobile navigation.

The standard Playwright browser download was unavailable in the workspace. Browser checks were run through Playwright using a locally installed Chromium 153 binary instead, with its software renderer; web security and CSP enforcement remained enabled. The committed test script also supports Playwright's normal Chromium installation for CI.

## Not executed in this workspace

- Docker image build/run and the separate real Docker CLI helper (no Docker daemon available).
- Trivy image/filesystem scanning and SBOM generation.
- Hosted GitHub Actions or Jenkins execution.
- SonarQube server analysis and quality gate.
- Registry publishing or Kubernetes/EKS deployment.
- TLS certificate/proxy verification on a public domain.
- Prometheus/Grafana live integration.
- Load, soak, adversarial tenant-isolation tests, or production backup/restore drills.

Passing source tests is not proof of those deployment outcomes. Run the supplied gates in your own environment before release. Dependency/advisory results are time-sensitive.

## Scope

The working terminal is a training simulator. There is no multi-tenant real Linux runtime, multiplayer matchmaking, high availability, email recovery service, or claim of an independent security audit. See `SECURITY.md` and `docs/REAL_SANDBOX.md` before expanding those boundaries.
