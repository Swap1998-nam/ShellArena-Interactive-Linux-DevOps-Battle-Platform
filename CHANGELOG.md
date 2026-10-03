# 2.0.0 — 2026-09-27

- Replaced the single terminal page with a responsive seven-view learning application.
- Added 16 missions, objective tracking, a persistent virtual filesystem, hints, bookmarks, XP, streaks, achievements, and opt-in leaderboard.
- Added guest profiles, account upgrade, registration, authentication, preferences, and progress export.
- Replaced unauthenticated WebSocket commands and direct web-to-Docker execution with a same-origin, bounded simulator API.
- Added SQLite persistence, ownership validation, transactional XP deduplication, security headers, CSRF controls, rate limits, and resource bounds.
- Added a unified non-root image, Compose setup, Kubernetes templates, GitHub Actions, Jenkins/SonarQube configuration, scanner gates, and SBOM generation.
- Added tests, browser checks, operator tooling, monitoring templates, and deployment documentation.

## Compatibility

The app is now one origin: port 3000 with Compose, port 8000 with the local runner. The former standalone backend port 5000, Socket.IO protocol, and independent frontend/backend Dockerfiles are no longer used. Existing v1 contained no account database to migrate. Real Docker execution is now a separate opt-in local tool, not the web terminal.
