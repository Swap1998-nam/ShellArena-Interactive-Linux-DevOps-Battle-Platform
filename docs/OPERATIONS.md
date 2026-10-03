# Operations

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_ENV` | `development` | `production` enables Secure cookies and HSTS and requires explicit keys/hosts |
| `SECRET_KEY` | Ephemeral in bare dev startup | At least 32 random characters; keep stable across restarts and all workers |
| `DATABASE_PATH` | `data/shellarena.db` | Writable persistent SQLite database |
| `TRUSTED_HOSTS` | Unrestricted in bare development | Comma-separated allowed hostnames; required in production |
| `PUBLIC_ORIGIN` | None | Exact public HTTPS origin behind a TLS terminator |
| `METRICS_TOKEN` | Disabled endpoint | Separate bearer token for `/metrics` |
| `WEB_WORKERS` | `2` | Gunicorn workers sharing the same SQLite file and signing key |

Use `scripts/bootstrap.py` to generate local keys. It never overwrites an existing `.env`. `scripts/serve.py` loads that file for local development. Docker Compose reads it automatically. The Kubernetes deployment gets its keys from a Secret.

## Health and logs

`/health/live` confirms the process is responding. `/health/ready` confirms database access. Readiness does not prove sufficient free disk capacity or a successful backup. Monitor disk space independently.

API responses carry `X-Request-ID`. The app emits structured JSON records with request ID, method, path, status, and duration. Commands, passwords, cookies, tokens, and bodies are not logged. Gunicorn emits access/process logs separately. Collect stdout/stderr centrally and set retention. Compose caps local logs at three 10 MB files.

## Backup and restore

Use the SQLite backup API rather than copying a live `.db` file without its WAL.

```bash
.venv/bin/python scripts/manage.py --database data/shellarena.db backup /secure-backups/shellarena-YYYYMMDD.db
```

The destination must not already exist. The parent directory must exist. Protect backup files and encrypt them using your platform's storage/key management. Schedule backups from your operator environment and perform a restore drill before onboarding users. Define the acceptable recovery point and recovery time for your deployment.

For a Compose deployment, you can use Python's SQLite backup API inside the running app container to create `/app/data/backup.db`, then copy that file out. Do not copy the live database with a plain file copy. The image intentionally does not include operator scripts or credentials.

To restore: stop the application; retain the current volume as a rollback copy; restore the selected consistent backup into a **fresh data directory/volume**; set UID/GID 10001 ownership for containers; start one app instance; verify login and saved mission progress. Using a fresh directory prevents stale WAL/SHM sidecars from being paired with a restored database. Restoring user state can also restore old session records; rotate the signing key to require a fresh sign-in after recovery.

## Cleanup and account recovery

```bash
.venv/bin/python scripts/manage.py --database data/shellarena.db cleanup
.venv/bin/python scripts/manage.py --database data/shellarena.db reset-password USERNAME
```

Cleanup removes expired sessions/rate buckets and guest profiles with no command activity for 30 days, including their dependent labs/progress. Registered accounts are kept. Schedule cleanup daily. Password recovery prompts interactively, never accepts a password in shell arguments, and revokes all account sessions. Perform your own identity verification before executing it.

## Monitoring

`/metrics` is disabled unless `METRICS_TOKEN` is set. Send `Authorization: Bearer TOKEN` to retrieve:

- `shellarena_registered_users` (gauge)
- `shellarena_completions` (gauge)

`monitoring/prometheus.yml` expects the same token mounted as `/run/secrets/shellarena_metrics_token`, and `alerts.yml` mounted at `/etc/prometheus/alerts.yml`. Prometheus must be attached to the application's Docker network or use an appropriate internal service address. Add its target hostname to `TRUSTED_HOSTS` (for Compose this is `app`) without opening the application port publicly. For Kubernetes, include the service DNS hostname in trusted hosts or explicitly configure a trusted Host header for your scraper. Permit the scraper's namespace in NetworkPolicy.

Import `monitoring/grafana-dashboard.json` into your existing Grafana and choose its Prometheus datasource. This release supplies configuration, not an already running monitoring cluster. Add gateway latency/error-rate and host/container CPU, memory, and disk metrics using your existing exporters.

The app rate limiter trusts only the socket peer. Proxy deployments share those limits unless a separately reviewed trusted-client-IP implementation is added. Do not increase quotas blindly; use edge per-client limits, load tests, and a shared limiter for larger traffic.

## Troubleshooting

- **Sign-in does not stick:** confirm a stable secret shared across workers; use HTTPS in production; verify the exact public host/origin.
- **403 on a mutation:** refresh after session rotation/expiry; check CSRF/header forwarding and the public origin.
- **429 behind an ingress:** the app sees the ingress peer; see the rate-limiting boundary above.
- **Database read-only/unable to open:** verify volume ownership, mount mode, free disk space, and the configured database path.
- **Unrecognized command:** type `help`; this is a bounded training simulator.
- **Sonar stage waits:** verify webhook reachability, configured server/tool names, and credentials.
- **Docker CLI lab fails:** confirm the opt-in variable, separately installed SDK, sandbox image, and your disposable rootless lab setup.
