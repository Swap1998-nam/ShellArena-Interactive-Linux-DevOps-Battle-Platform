import concurrent.futures
import sqlite3
import pytest
from backend.app import create_app

SOLUTIONS = {
    "first-contact": ["pwd", "whoami", "ls"],
    "read-the-signals": ["cat /var/log/app.log", "grep ERROR /var/log/app.log", "tail -n 3 /var/log/app.log"],
    "release-workspace": ["mkdir releases", "cp config.env releases/config.env", "touch releases/READY"],
    "least-privilege": ["chmod 600 config.env", "stat config.env"],
    "error-budget": ["wc -l /var/log/app.log", "grep ERROR /var/log/app.log | wc -l"],
    "release-note": ["echo release-ready > release.txt", "cat release.txt"],
    "disk-detective": ["df -h", "du -sh /var/log"],
    "process-patrol": ["ps aux", "ps aux | grep worker"],
    "container-recon": ["docker ps", "docker images", "docker logs web"],
    "container-inspect": ["docker ps -a", "docker inspect web", "docker logs web | grep ERROR"],
    "pod-patrol": ["kubectl get pods", "kubectl describe pod api-7d9", "kubectl logs api-7d9"],
    "cluster-map": ["kubectl get nodes", "kubectl get services", "kubectl get deployments"],
    "git-recon": ["git status", "git log --oneline", "git branch"],
    "secret-hunt": ["cat demo.env", "grep DEMO_TOKEN demo.env", "chmod 600 demo.env"],
    "health-triage": ["uname -a", "df -h", "ps aux", "grep ERROR /var/log/app.log"],
    "delivery-preflight": [
        "git status",
        "docker images",
        "kubectl get deployments",
        "echo release-ready > release.txt",
    ],
}


@pytest.mark.parametrize("mission,commands", SOLUTIONS.items())
def test_every_mission_is_solvable_and_rewards_once(api, mission, commands):
    lab = api("/labs", {"mission_id": mission}).json
    for command in commands:
        result = api(f"/labs/{lab['id']}/commands", {"command": command})
        assert result.status_code == 200, result.json
        assert result.json["exit_code"] == 0, result.json
    assert result.json["completed"]
    xp = result.json["awarded_xp"]
    assert xp > 0
    assert api(f"/labs/{lab['id']}/commands", {"command": commands[-1]}).json["awarded_xp"] == 0
    assert api("/overview").json["stats"]["xp"] == xp


def test_isolation_csrf_and_hidden_rules(app, api):
    lab = api("/labs", {"mission_id": "first-contact"}).json
    stranger = app.test_client()
    session = stranger.post("/api/session", json={}, headers={"X-ShellArena": "1"}).json
    headers = {"X-ShellArena": "1", "X-CSRF-Token": session["csrf"]}
    assert stranger.get(f"/api/labs/{lab['id']}").status_code == 404
    assert stranger.post(f"/api/labs/{lab['id']}/commands", json={"command": "pwd"}, headers=headers).status_code == 404
    assert (
        api.client.post(
            f"/api/labs/{lab['id']}/commands", json={"command": "pwd"}, headers={"X-ShellArena": "1"}
        ).status_code
        == 403
    )
    missions = api("/overview").json["missions"]
    assert isinstance(missions[0]["objectives"][0], str)
    assert "hints" not in missions[0]
    assert "rule" not in str(missions)


def test_account_upgrade_persistence_login_and_revocation(app, api):
    lab = api("/labs", {"mission_id": "first-contact"}).json
    for c in SOLUTIONS["first-contact"]:
        api(f"/labs/{lab['id']}/commands", {"command": c})
    assert api("/auth/register", {"username": "x", "password": "short"}).status_code == 400
    result = api("/auth/register", {"username": "Engineer", "password": "a-long-unique-passphrase"})
    assert result.status_code == 201
    api.headers["X-CSRF-Token"] = result.json["csrf"]
    assert api("/overview").json["stats"]["xp"] == 100
    old_cookie = api.client.get_cookie("shellarena_session").value
    assert api("/auth/logout", {}).status_code == 200
    attacker = app.test_client()
    attacker.set_cookie("shellarena_session", old_cookie)
    assert attacker.get("/api/overview").status_code == 401
    session = api("/session", {}).json
    api.headers["X-CSRF-Token"] = session["csrf"]
    assert api("/auth/login", {"username": "Engineer", "password": "wrong"}).status_code == 401
    result = api("/auth/login", {"username": "engineer", "password": "a-long-unique-passphrase"})
    assert result.status_code == 200
    assert api("/overview").json["stats"]["completed"] == 1
    with sqlite3.connect(app.config["DATABASE"]) as db:
        password = db.execute("SELECT password_hash FROM users WHERE username=?", ("Engineer",)).fetchone()[0]
        assert password.startswith("scrypt:")
        assert password != "a-long-unique-passphrase"


def test_hints_replay_reset_and_resume(api):
    lab = api("/labs", {"mission_id": "first-contact"}).json
    assert api("/labs", {"mission_id": "first-contact"}).json["id"] == lab["id"]
    hints = api(f"/labs/{lab['id']}/hint", {}).json
    assert hints["hints_used"] == 1
    assert len(api(f"/labs/{lab['id']}").json["hints"]) == 1
    for c in SOLUTIONS["first-contact"]:
        result = api(f"/labs/{lab['id']}/commands", {"command": c})
    assert result.json["awarded_xp"] == 90
    reset = api("/labs", {"mission_id": "first-contact", "reset": True}).json
    assert reset["history"] == []
    assert reset["checks"] == [False] * 3
    for c in SOLUTIONS["first-contact"]:
        result = api(f"/labs/{reset['id']}/commands", {"command": c})
    assert result.json["awarded_xp"] == 0
    assert api("/overview").json["stats"]["xp"] == 90


def test_opt_in_leaderboard_bookmarks_settings_and_export(api):
    assert api("/leaderboard").json["entries"] == []
    assert api("/settings", {"public": True, "compact": False}).status_code == 400
    result = api("/auth/register", {"username": "Operator", "password": "a-long-unique-passphrase"})
    api.headers["X-CSRF-Token"] = result.json["csrf"]
    assert api("/leaderboard").json["entries"] == []
    assert api("/settings", {"public": True, "compact": True}).status_code == 200
    assert api("/leaderboard").json["entries"][0]["name"] == "Operator"
    assert api("/bookmarks/first-contact", {"saved": True}).status_code == 200
    assert api("/overview").json["bookmarks"] == ["first-contact"]
    assert api("/bookmarks/first-contact", {"saved": False}).status_code == 200
    assert api("/overview").json["bookmarks"] == []
    export = api("/export").json
    assert "password" not in str(export)
    assert "csrf" not in str(export)
    assert export["profile"]["compact"]
    assert api("/settings", {"public": False, "compact": False}).status_code == 200
    assert api("/leaderboard").json["entries"] == []


def test_invalid_payloads_and_security_headers(api, client):
    assert (
        client.post(
            "/api/session", json={}, headers={"X-ShellArena": "1", "Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.post("/api/session", json={}, headers={"X-ShellArena": "1", "Sec-Fetch-Site": "cross-site"}).status_code
        == 403
    )
    assert client.post("/api/session", json={}).status_code == 403
    assert api("/labs", {"mission_id": "does-not-exist"}).status_code == 404
    assert api("/labs", {"mission_id": 12}).status_code == 400
    assert api("/labs", {"mission_id": "first-contact", "reset": "yes"}).status_code == 400
    assert api("/settings", {"public": 1, "compact": 0}).status_code == 400
    assert api("/bookmarks/nope", {"saved": True}).status_code == 404
    assert api("/bookmarks/first-contact", {"saved": "yes"}).status_code == 400
    assert api("/labs", []).status_code == 400
    lab = api("/labs", {"mission_id": "first-contact"}).json
    assert api(f"/labs/{lab['id']}/commands", {"command": "x" * 513}).status_code == 400
    assert api(f"/labs/{lab['id']}/commands", {"command": ""}).status_code == 400
    assert api("/labs", {"mission_id": "x" * 10000}).status_code == 413
    response = client.get("/")
    assert response.status_code == 200
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Frame-Options"] == "DENY"
    assert client.get("/../backend/app.py").status_code == 404
    assert client.get("/health/ready").status_code == 200
    assert client.get("/metrics").status_code == 404


def test_database_persists_across_app_restarts(app, api):
    api("/bookmarks/first-contact", {"saved": True})
    new_app = create_app({**app.config, "TESTING": True})
    other = new_app.test_client()
    other.set_cookie("shellarena_session", api.client.get_cookie("shellarena_session").value)
    assert other.get("/api/overview").json["bookmarks"] == ["first-contact"]


def test_concurrent_completion_only_awards_once(app, api):
    lab = api("/labs", {"mission_id": "first-contact"}).json
    for c in ["pwd", "whoami"]:
        api(f"/labs/{lab['id']}/commands", {"command": c})
    cookie = api.client.get_cookie("shellarena_session").value

    def finish(_):
        client = app.test_client()
        client.set_cookie("shellarena_session", cookie)
        return client.post(f"/api/labs/{lab['id']}/commands", json={"command": "ls"}, headers=api.headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(finish, range(4)))
    assert all(r.status_code == 200 for r in results)
    assert sum(r.json["awarded_xp"] for r in results) == 100
    assert api("/overview").json["stats"]["xp"] == 100


def test_production_fails_closed(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app()
    monkeypatch.setenv("SECRET_KEY", "x" * 40)
    monkeypatch.delenv("TRUSTED_HOSTS", raising=False)
    with pytest.raises(RuntimeError, match="TRUSTED_HOSTS"):
        create_app()


def test_rate_limit_across_clients_and_metrics(app, monkeypatch):
    app.config["RATE_LIMIT_ENABLED"] = True
    for _ in range(20):
        client = app.test_client()
        assert client.post("/api/session", json={}, headers={"X-ShellArena": "1"}).status_code == 200
    response = app.test_client().post("/api/session", json={}, headers={"X-ShellArena": "1"})
    assert response.status_code == 429
    assert response.headers["Retry-After"]
    monkeypatch.setenv("METRICS_TOKEN", "metrics-test-only")
    assert app.test_client().get("/metrics", headers={"Authorization": "Bearer metrics-test-only"}).status_code == 200
