# ShellArena 2.0

**Your terminal. Your proving ground.**

A complete, stateful Linux & DevOps practice application with a redesigned responsive interface, 16 guided missions, accounts, progress tracking, and a DevSecOps delivery foundation.

> **Runtime boundary:** the web terminal is a bounded, server-side **simulator**. It never executes host commands. Docker, Kubernetes, Git, and host-inspection commands return explicitly labelled practice snapshots. A separate, opt-in Docker CLI runner is supplied for disposable local labs; it is not connected to the web application.

## Start in two commands

Install Docker Engine with the Compose plugin and Python 3, then run from the project root:

```bash
python3 scripts/bootstrap.py
docker compose up --build -d
```

Open **http://localhost:3000**. Explore immediately as a guest; create an account to retain that progress across devices. The application binds to loopback by default. Do not expose development mode to the internet.

```bash
docker compose logs -f app
docker compose down                 # preserves account and progress data
```

Do not use `docker compose down -v` unless you intend to delete the database volume.

## Run without Docker

Python 3.12+ is recommended. On Windows use WSL2 or Docker Desktop; Gunicorn requires a Unix-like environment.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/serve.py
```

Open **http://localhost:8000**. The startup script creates a private `.env` if needed. The database is `data/shellarena.db`. Keep both when restarting. Do not commit them.

## What works

| Area | Included behavior |
| --- | --- |
| Overview | Live account stats, daily mission rotation, weekly completion activity, skill progress |
| Mission library | 16 missions across Linux, Docker, Kubernetes, Git, Security, and DevOps; search, category/difficulty filters, bookmarks |
| Practice arena | Persistent virtual filesystem, command history, pipes, redirection, `&&`, guided objectives, hints, restart, completion feedback |
| Progress | Server-validated objectives, one-time XP, hint penalties, levels, UTC daily streaks, 4 achievements |
| Accounts | Guest exploration, guest-to-account upgrade, scrypt password hashing, sign-in, server-revoked sign-out |
| Leaderboard | Opt-in public usernames and scores; no fabricated members or scores |
| Preferences | Compact cards, leaderboard privacy, JSON progress export |
| Responsive UI | Desktop/tablet/mobile navigation, keyboard terminal history, Ctrl/Cmd+K search, reduced-motion support, local fonts |
| Operations | Persistent SQLite WAL storage, health/readiness routes, request IDs and structured logs, protected metrics, backup/cleanup/reset tools |
| Delivery | Non-root container, Docker Compose, GitHub Actions, Jenkins, SonarQube configuration, Trivy/SBOM gates, Kubernetes templates |

## Mission tracks

- **Linux:** navigation, reading logs, file operations, pipes, redirection, disk and process diagnosis, incident preflight.
- **Docker:** container inventory, logs, and inspection using fixed practice snapshots.
- **Kubernetes:** pod troubleshooting and cluster discovery using fixed practice snapshots.
- **Security:** file permissions and a fictional secret-detection exercise.
- **Git:** working tree, branch, and commit history inspection using fixed practice snapshots.
- **DevOps:** a combined release preflight.

Type `help` in the arena for supported commands. This is not a complete Bash implementation: no command substitution, arbitrary programs, network calls, interactive editors, jobs, glob expansion, or full POSIX semantics. State persists in one active lab per account. Starting another mission replaces the previous unfinished lab; completed missions, XP, and bookmarks remain saved.

XP is awarded only the first time each mission is completed. Hints deduct 10 XP each from that first award. Replays earn no additional XP. Daily missions rotate at midnight UTC and use normal mission rewards; daily bonus XP is not implemented.

## Verify changes

```bash
make test
make lint
make security
npm ci --ignore-scripts
npx playwright install --with-deps chromium
npm run test:browser
```

Browser tests start an isolated Gunicorn server with two workers, a temporary database, and disposable credentials. They save screenshots to `test-results/`. They do not modify your working application database.

See [validation record](docs/VALIDATION.md) for checks actually executed for this release and checks that still need your deployment environment.

## Ship it deliberately

This is a **single-instance beta foundation**, not a claim of audited or highly available production readiness. It includes a working app and delivery configuration, but production credentials, a domain, TLS, registry publishing, cluster integration, image scans, restore drills, and load testing must be verified in your environment.

- [DevSecOps setup: Jenkins, SonarQube, Trivy, and GitHub Actions](docs/DEVSECOPS.md)
- [Deployment: local host, HTTPS, Kubernetes, and EKS considerations](docs/DEPLOYMENT.md)
- [Operations: configuration, backup, recovery, and monitoring](docs/OPERATIONS.md)
- [Architecture and API](docs/ARCHITECTURE.md)
- [Real Linux sandbox boundary](docs/REAL_SANDBOX.md)
- [Security model and disclosure](SECURITY.md)
- [Release changes](CHANGELOG.md)

## Repository map

```text
backend/                 Flask API, missions, persistence, practice engine
frontend/                Same-origin UI, CSS, local fonts, SVG assets
tests/                   API/security regression tests and browser workflows
scripts/                 Local startup and operator tools
deploy/kubernetes/       Restricted single-replica deployment templates
monitoring/              Prometheus scrape/alert config and Grafana dashboard
docs/                    Architecture, deployment, operations, validation
Dockerfile               Unified non-root application image
Jenkinsfile              Test → security → browser → quality gate → image → optional push
.github/workflows/ci.yml  Pull request checks and container-security gates
```

The existing repository's Flask foundation is retained. The original direct Docker socket exposure and the disconnected frontend/backend WebSocket setup have been replaced by one same-origin application. No existing database migration is needed from the original prototype because it had no persistence.
