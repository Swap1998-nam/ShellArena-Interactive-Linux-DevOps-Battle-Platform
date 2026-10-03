# Security model

The public web application never calls a host shell, subprocess runner, or Docker daemon. Its terminal is a deterministic training interpreter operating on a size-bounded JSON workspace stored in SQLite. Browser-visible command output is escaped before rendering. Client-side XP or completion flags are not trusted.

## Implemented controls

- Opaque session tokens stored as SHA-256 digests in the database, signed HttpOnly/SameSite cookies, 7-day server expiry, token rotation on authentication, revocation on logout.
- Scrypt password hashes; 12–128-character passwords; account identifiers restricted to a small ASCII alphabet; generic sign-in failure messages.
- Same-origin JSON requests, a custom request header, CSRF verification on all state changes after session creation, and cross-site request rejection. No permissive CORS configuration.
- Production startup rejects missing/short signing keys and missing host configuration. Production cookies require HTTPS.
- CSP without external scripts or inline script/style allowances, clickjacking protection, MIME-sniffing protection, production HSTS.
- Parameterized SQL; ownership checks on labs; transactional command updates and unique completion keys; no double XP under concurrent requests.
- Shared database rate limits across workers; input, file-count, directory-count, file-size, workspace-size, command-output, history, and activity-log bounds.
- Non-root application image; read-only container root filesystem, dropped capabilities, no privilege escalation, CPU/memory/PID limits; no Docker socket mount.
- Protected aggregate metrics, no account leaderboard exposure without opt-in, no third-party analytics.

## Limits that matter

SQLite and its database-backed rate limiter target one small deployment. Behind a reverse proxy, the application deliberately uses the proxy's peer address rather than trusting arbitrary forwarded IP headers, so clients behind the same proxy share IP quotas. Configure a trusted gateway/WAF with per-client throttling, then explicitly design trusted-proxy handling and distributed limits before a larger public launch. Do not simply trust every `X-Forwarded-For` value.

The leaderboard measures completion of guided practice objectives, not tamper-proof exams or certifications. Mission answers are visible in the source and hints. There is no prize, payment, assessment attestation, or competitive integrity guarantee.

Account recovery is operator-assisted through `scripts/manage.py reset-password`. Email verification, self-service recovery, account deletion UI, MFA, SSO, abuse moderation, billing, multiplayer battles, and real interactive PTYs are not implemented. Operators should establish identity checks before password resets and a user-data deletion process before public onboarding.

The Docker CLI lab helper is not a secure boundary for adversarial public tenants. See `docs/REAL_SANDBOX.md`. Its container limits do not eliminate kernel/container escape risk.

Do not publish `.env`, SQLite files/backups, bearer tokens, or registry credentials. Database files contain sensitive account hashes and user activity. Restrict permissions, encrypt storage/backups through your hosting platform, and define retention.

## Scanner exceptions

The only Bandit B108 exceptions identify `/tmp` as a virtual filesystem label or as an isolated container tmpfs mount. Neither is a host temporary-file operation. They are locally annotated; the rule remains enabled for the rest of the source.

## Reporting

Use the repository owner's private security reporting channel if enabled. Otherwise contact the owner privately before sharing an exploitable issue. Do not post credentials, personal data, or exploit details in a public issue.

## Primary references

- https://flask.palletsprojects.com/en/stable/web-security/
- https://docs.docker.com/engine/security/
- https://docs.docker.com/engine/security/rootless/
- https://docs.github.com/en/actions/reference/security/secure-use
