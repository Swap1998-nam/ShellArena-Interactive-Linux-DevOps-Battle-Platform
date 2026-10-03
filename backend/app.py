"""Same-origin ShellArena API and frontend. Run with a production WSGI server."""

import datetime as dt
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
import uuid

from flask import Flask, g, jsonify, request, send_from_directory, session
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from .challenges import BY_ID, MISSIONS, public_mission, validate
from .simulator import execute, initial_state

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, username TEXT UNIQUE COLLATE NOCASE, password_hash TEXT,
 created_at INTEGER NOT NULL, last_seen INTEGER NOT NULL,
 public INTEGER NOT NULL DEFAULT 0, compact INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS sessions (
 token TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 csrf TEXT NOT NULL, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS labs (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 mission_id TEXT NOT NULL, state TEXT NOT NULL, checks TEXT NOT NULL,
 hints INTEGER NOT NULL DEFAULT 0, commands INTEGER NOT NULL DEFAULT 0,
 started_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS one_lab_per_user ON labs(user_id);
CREATE TABLE IF NOT EXISTS completions (
 user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, mission_id TEXT NOT NULL,
 xp INTEGER NOT NULL, completed_at INTEGER NOT NULL, PRIMARY KEY(user_id, mission_id));
CREATE TABLE IF NOT EXISTS bookmarks (
 user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, mission_id TEXT NOT NULL,
 PRIMARY KEY(user_id, mission_id));
CREATE TABLE IF NOT EXISTS activity (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 kind TEXT NOT NULL, mission_id TEXT, detail TEXT NOT NULL, created_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS activity_user_time ON activity(user_id, created_at);
CREATE TABLE IF NOT EXISTS rate_limits (key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires INTEGER NOT NULL);
PRAGMA user_version=1;
"""


class APIError(Exception):
    def __init__(self, message, status=400, retry_after=60):
        self.message, self.status, self.retry_after = message, status, retry_after


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    production = os.getenv("APP_ENV", "development") == "production"
    secret = os.getenv("SECRET_KEY", "")
    if production and len(secret) < 32 and not test_config:
        raise RuntimeError("Set SECRET_KEY to a random value of at least 32 characters in production.")
    if production and not os.getenv("TRUSTED_HOSTS") and not test_config:
        raise RuntimeError("Set TRUSTED_HOSTS to your production domain.")
    app.config.update(
        SECRET_KEY=secret or secrets.token_hex(32),
        DATABASE=os.getenv("DATABASE_PATH", str(ROOT / "data" / "shellarena.db")),
        SESSION_COOKIE_NAME="shellarena_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,
        MAX_CONTENT_LENGTH=8192,
        PERMANENT_SESSION_LIFETIME=dt.timedelta(days=7),
        TRUSTED_HOSTS=[x.strip() for x in os.getenv("TRUSTED_HOSTS", "").split(",") if x.strip()] or None,
        RATE_LIMIT_ENABLED=True,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(app.config["DATABASE"]) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            raise RuntimeError("Unsupported database schema version; see docs/OPERATIONS.md.")
        connection.executescript(SCHEMA)
    dummy_hash = generate_password_hash(secrets.token_hex(20))

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"], timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys=ON")
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        if connection := g.pop("db", None):
            connection.close()

    def rate_limit(scope, maximum, window=60):
        if not app.config["RATE_LIMIT_ENABLED"]:
            return
        now = int(time.time())
        # Only the actual peer address is trusted; forwarded headers are ignored.
        key = hashlib.sha256(f"{request.remote_addr}:{scope}:{now // window}".encode()).hexdigest()
        row = (
            db()
            .execute(
                "INSERT INTO rate_limits VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1 RETURNING count",
                (key, now + window),
            )
            .fetchone()
        )
        db().execute("DELETE FROM rate_limits WHERE expires < ?", (now,))
        db().commit()
        if row["count"] > maximum:
            raise APIError("Too many requests. Please wait before trying again.", 429, window - now % window)

    def get_user(required=True):
        if not hasattr(g, "user"):
            token = session.get("token", "")
            g.user = (
                db()
                .execute(
                    "SELECT u.*, s.csrf FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token=? AND s.expires>?",
                    (hashlib.sha256(token.encode()).hexdigest(), int(time.time())),
                )
                .fetchone()
            )
        if required and g.user is None:
            raise APIError("Your session expired. Refresh to start a new session.", 401)
        return g.user

    def payload():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise APIError("Send a JSON object.")
        return data

    def field(data, key, maximum=1024):
        value = data.get(key, "")
        if not isinstance(value, str) or len(value) > maximum:
            raise APIError(f"Invalid {key}.")
        return value.strip() if key != "password" else value

    def set_session(user_id):
        old = session.get("token")
        if old:
            db().execute("DELETE FROM sessions WHERE token=?", (hashlib.sha256(old.encode()).hexdigest(),))
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        db().execute(
            "INSERT INTO sessions VALUES (?,?,?,?)",
            (hashlib.sha256(token.encode()).hexdigest(), user_id, csrf, int(time.time()) + 604800),
        )
        db().execute("DELETE FROM sessions WHERE expires < ?", (int(time.time()),))
        session.clear()
        session["token"] = token
        session.permanent = True
        db().commit()
        if hasattr(g, "user"):
            del g.user
        return csrf

    def activity(user_id, kind, mission_id, detail):
        db().execute(
            "INSERT INTO activity(user_id,kind,mission_id,detail,created_at) VALUES (?,?,?,?,?)",
            (user_id, kind, mission_id, detail, int(time.time())),
        )
        db().execute(
            "DELETE FROM activity WHERE user_id=? AND id NOT IN (SELECT id FROM activity WHERE user_id=? ORDER BY id DESC LIMIT 200)",
            (user_id, user_id),
        )

    @app.before_request
    def protect():
        g.started = time.monotonic()
        g.request_id = uuid.uuid4().hex[:16]
        if request.path.startswith("/api/"):
            rate_limit("api", 240)
            if request.method not in ("GET", "HEAD", "OPTIONS"):
                if request.headers.get("X-ShellArena") != "1" or not request.is_json:
                    raise APIError("A same-origin JSON request is required.", 403)
                if request.headers.get("Sec-Fetch-Site") == "cross-site":
                    raise APIError("Cross-site requests are not allowed.", 403)
                origin = request.headers.get("Origin")
                if origin and origin.rstrip("/") != request.host_url.rstrip("/"):
                    # TLS terminators preserve Host; compare exact origin against configured PUBLIC_ORIGIN.
                    if origin != os.getenv("PUBLIC_ORIGIN", ""):
                        raise APIError("Untrusted request origin.", 403)
                if request.path != "/api/session":
                    user = get_user()
                    supplied = request.headers.get("X-CSRF-Token", "")
                    if not secrets.compare_digest(supplied, user["csrf"]):
                        raise APIError("Session verification failed. Refresh and try again.", 403)

    @app.after_request
    def headers(response):
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "same-origin",
                "X-Frame-Options": "DENY",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",
                "X-Request-ID": getattr(g, "request_id", ""),
            }
        )
        if production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        app.logger.info(
            json.dumps(
                {
                    "request_id": getattr(g, "request_id", ""),
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - getattr(g, "started", time.monotonic())) * 1000, 2),
                }
            )
        )
        return response

    @app.errorhandler(APIError)
    def api_error(error):
        response = jsonify(error=error.message, request_id=getattr(g, "request_id", ""))
        if error.status == 429:
            response.headers["Retry-After"] = str(error.retry_after)
        return response, error.status

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description, request_id=getattr(g, "request_id", "")), error.code

    @app.errorhandler(Exception)
    def unexpected(error):
        app.logger.exception("Request failed: %s", getattr(g, "request_id", ""))
        return jsonify(error="Something went wrong. Try again shortly.", request_id=getattr(g, "request_id", "")), 500

    @app.get("/health/live")
    def live():
        return {"status": "ok", "version": "2.0.0"}

    @app.get("/health/ready")
    def ready():
        db().execute("SELECT 1 FROM users LIMIT 1")
        return {"status": "ready", "mode": "simulator"}

    @app.get("/metrics")
    def metrics():
        expected = os.getenv("METRICS_TOKEN", "")
        if not expected or not secrets.compare_digest(request.headers.get("Authorization", ""), f"Bearer {expected}"):
            raise APIError("Not found.", 404)
        users = db().execute("SELECT COUNT(*) FROM users WHERE username IS NOT NULL").fetchone()[0]
        completions = db().execute("SELECT COUNT(*) FROM completions").fetchone()[0]
        return (
            (
                "# HELP shellarena_registered_users Registered accounts.\n# TYPE shellarena_registered_users gauge\n"
                f"shellarena_registered_users {users}\n"
                "# HELP shellarena_completions Completed missions.\n# TYPE shellarena_completions gauge\n"
                f"shellarena_completions {completions}\n"
            ),
            200,
            {"Content-Type": "text/plain; version=0.0.4"},
        )

    @app.post("/api/session")
    def start_session():
        payload()
        user = get_user(False)
        if not user:
            rate_limit("new-session", 20, 3600)
            uid, now = uuid.uuid4().hex, int(time.time())
            db().execute("INSERT INTO users(id,created_at,last_seen) VALUES (?,?,?)", (uid, now, now))
            set_session(uid)
            user = get_user()
        return {"csrf": user["csrf"], "user": user_info(user)}

    def user_info(user):
        return {
            "id": user["id"],
            "name": user["username"] or "Explorer",
            "guest": user["username"] is None,
            "public": bool(user["public"]),
            "compact": bool(user["compact"]),
        }

    @app.post("/api/auth/register")
    def register():
        rate_limit("auth", 10, 600)
        user, data = get_user(), payload()
        if user["username"]:
            raise APIError("You already have an account.")
        name, password = field(data, "username", 24), field(data, "password", 128)
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{2,23}", name):
            raise APIError("Use 3–24 letters, numbers, or underscores; start with a letter.")
        if len(password) < 12:
            raise APIError("Use a password with at least 12 characters.")
        try:
            db().execute(
                "UPDATE users SET username=?,password_hash=? WHERE id=?",
                (name, generate_password_hash(password), user["id"]),
            )
            activity(user["id"], "account", None, "Created a permanent account")
            csrf = set_session(user["id"])
        except sqlite3.IntegrityError:
            db().rollback()
            raise APIError("That username is unavailable.", 409) from None
        return {"csrf": csrf, "user": user_info(get_user())}, 201

    @app.post("/api/auth/login")
    def login():
        rate_limit("auth", 10, 600)
        data = payload()
        name, password = field(data, "username", 24), field(data, "password", 128)
        account_key = hashlib.sha256(name.lower().encode()).hexdigest()
        # Same database-backed bucket is shared by every WSGI worker.
        rate_limit("account-" + account_key, 5, 600)
        user = db().execute("SELECT * FROM users WHERE username=?", (name,)).fetchone()
        valid = check_password_hash(user["password_hash"] if user else dummy_hash, password)
        if not user or not valid:
            raise APIError("Incorrect username or password.", 401)
        csrf = set_session(user["id"])
        return {"csrf": csrf, "user": user_info(get_user())}

    @app.post("/api/auth/logout")
    def logout():
        token = session.get("token", "")
        db().execute("DELETE FROM sessions WHERE token=?", (hashlib.sha256(token.encode()).hexdigest(),))
        db().commit()
        session.clear()
        return {"ok": True}

    def overview(user):
        uid = user["id"]
        completions = [
            dict(x)
            for x in db().execute(
                "SELECT mission_id,xp,completed_at FROM completions WHERE user_id=? ORDER BY completed_at DESC", (uid,)
            )
        ]
        activity_rows = [
            dict(x)
            for x in db().execute(
                "SELECT kind,mission_id,detail,created_at FROM activity WHERE user_id=? ORDER BY id DESC LIMIT 50",
                (uid,),
            )
        ]
        total = sum(x["xp"] for x in completions)
        days = {dt.datetime.fromtimestamp(x["completed_at"], dt.timezone.utc).date() for x in completions}
        today = dt.datetime.now(dt.timezone.utc).date()
        day = today if today in days else today - dt.timedelta(days=1)
        streak = 0
        while day in days:
            streak += 1
            day -= dt.timedelta(days=1)
        week = [
            {
                "date": (today - dt.timedelta(days=6 - i)).isoformat(),
                "count": sum(
                    dt.datetime.fromtimestamp(x["completed_at"], dt.timezone.utc).date()
                    == today - dt.timedelta(days=6 - i)
                    for x in completions
                ),
            }
            for i in range(7)
        ]
        active = db().execute("SELECT id,mission_id FROM labs WHERE user_id=?", (uid,)).fetchone()
        return {
            "user": user_info(user),
            "missions": [public_mission(x) for x in MISSIONS],
            "completions": completions,
            "bookmarks": [x[0] for x in db().execute("SELECT mission_id FROM bookmarks WHERE user_id=?", (uid,))],
            "stats": {"xp": total, "level": total // 500 + 1, "completed": len(completions), "streak": streak},
            "week": week,
            "activity": activity_rows,
            "active": dict(active) if active else None,
            "daily_id": MISSIONS[today.toordinal() % len(MISSIONS)]["id"],
            "mode": "simulator",
        }

    @app.get("/api/overview")
    def get_overview():
        return overview(get_user())

    @app.post("/api/bookmarks/<mission_id>")
    def bookmark(mission_id):
        if mission_id not in BY_ID:
            raise APIError("Mission not found.", 404)
        user, data = get_user(), payload()
        if not isinstance(data.get("saved"), bool):
            raise APIError("saved must be true or false.")
        if data["saved"]:
            db().execute("INSERT OR IGNORE INTO bookmarks VALUES (?,?)", (user["id"], mission_id))
        else:
            db().execute("DELETE FROM bookmarks WHERE user_id=? AND mission_id=?", (user["id"], mission_id))
        db().commit()
        return {"saved": data["saved"]}

    @app.post("/api/settings")
    def settings():
        data, user = payload(), get_user()
        if not isinstance(data.get("public"), bool) or not isinstance(data.get("compact"), bool):
            raise APIError("Settings must be true or false.")
        if data["public"] and user["username"] is None:
            raise APIError("Create an account before joining the leaderboard.")
        db().execute("UPDATE users SET public=?,compact=? WHERE id=?", (data["public"], data["compact"], user["id"]))
        db().commit()
        return {"ok": True}

    @app.get("/api/leaderboard")
    def leaderboard():
        get_user()
        rows = db().execute(
            "SELECT u.username AS name,COALESCE(SUM(c.xp),0) AS xp,COUNT(c.mission_id) AS completed "
            "FROM users u LEFT JOIN completions c ON u.id=c.user_id "
            "WHERE u.public=1 AND u.username IS NOT NULL GROUP BY u.id ORDER BY xp DESC,u.username COLLATE NOCASE LIMIT 50"
        )
        return {"entries": [dict(x) for x in rows]}

    def lab_info(row):
        state = json.loads(row["state"])
        return {
            "id": row["id"],
            "mission_id": row["mission_id"],
            "cwd": state["cwd"],
            "checks": json.loads(row["checks"]),
            "hints_used": row["hints"],
            "hints": BY_ID[row["mission_id"]]["hints"][: row["hints"]],
            "commands": row["commands"],
            "history": state["history"],
            "started_at": row["started_at"],
        }

    def own_lab(lab_id):
        row = db().execute("SELECT * FROM labs WHERE id=? AND user_id=?", (lab_id, get_user()["id"])).fetchone()
        if row is None:
            raise APIError("Practice session not found. Start the mission again.", 404)
        return row

    @app.post("/api/labs")
    def start_lab():
        user, data = get_user(), payload()
        mission_id = field(data, "mission_id", 80)
        if mission_id not in BY_ID:
            raise APIError("Mission not found.", 404)
        reset = data.get("reset", False)
        if not isinstance(reset, bool):
            raise APIError("reset must be true or false.")
        # Serialize session replacement against concurrent command requests.
        db().execute("BEGIN IMMEDIATE")
        row = db().execute("SELECT * FROM labs WHERE user_id=?", (user["id"],)).fetchone()
        if row and row["mission_id"] == mission_id and not reset:
            return lab_info(row)
        now, lab_id = int(time.time()), uuid.uuid4().hex
        db().execute("DELETE FROM labs WHERE user_id=?", (user["id"],))
        db().execute(
            "INSERT INTO labs(id,user_id,mission_id,state,checks,started_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (
                lab_id,
                user["id"],
                mission_id,
                json.dumps(initial_state()),
                json.dumps([False] * len(BY_ID[mission_id]["objectives"])),
                now,
                now,
            ),
        )
        activity(user["id"], "started", mission_id, "Started " + BY_ID[mission_id]["title"])
        db().commit()
        return lab_info(own_lab(lab_id)), 201

    @app.get("/api/labs/<lab_id>")
    def get_lab(lab_id):
        return lab_info(own_lab(lab_id))

    @app.post("/api/labs/<lab_id>/hint")
    def hint(lab_id):
        payload()
        db().execute("BEGIN IMMEDIATE")
        row = own_lab(lab_id)
        hints = BY_ID[row["mission_id"]]["hints"]
        count = min(row["hints"] + 1, len(hints))
        db().execute("UPDATE labs SET hints=? WHERE id=?", (count, lab_id))
        db().commit()
        return {"hints": hints[:count], "hints_used": count}

    @app.post("/api/labs/<lab_id>/commands")
    def command(lab_id):
        rate_limit("commands", 60)
        command_text = field(payload(), "command", 512)
        if not command_text:
            raise APIError("Enter a command first.")
        db().execute("BEGIN IMMEDIATE")
        row = own_lab(lab_id)
        state, mission = json.loads(row["state"]), BY_ID[row["mission_id"]]
        output, exit_code = execute(state, command_text)
        checks = validate(mission, state, command_text, exit_code, json.loads(row["checks"]))
        awarded = 0
        complete = all(checks)
        now, user = int(time.time()), get_user()
        if complete:
            xp = max(0, mission["xp"] - row["hints"] * 10)
            inserted = db().execute(
                "INSERT OR IGNORE INTO completions VALUES (?,?,?,?)", (user["id"], mission["id"], xp, now)
            )
            if inserted.rowcount:
                awarded = xp
                activity(user["id"], "completed", mission["id"], f"Completed {mission['title']} · +{xp} XP")
        state["history"] = (state["history"] + [{"command": command_text, "output": output, "exit_code": exit_code}])[
            -40:
        ]
        db().execute(
            "UPDATE labs SET state=?,checks=?,commands=commands+1,updated_at=? WHERE id=?",
            (json.dumps(state), json.dumps(checks), now, lab_id),
        )
        db().execute("UPDATE users SET last_seen=? WHERE id=?", (now, user["id"]))
        db().commit()
        return {
            "output": output,
            "exit_code": exit_code,
            "checks": checks,
            "cwd": state["cwd"],
            "completed": complete,
            "awarded_xp": awarded,
            "commands": row["commands"] + 1,
        }

    @app.get("/api/export")
    def export():
        user = get_user()
        data = overview(user)
        data.pop("user")
        data.pop("missions")
        return {
            "profile": user_info(user),
            "progress": data,
            "exported_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }

    @app.get("/")
    def index():
        return send_from_directory(ROOT / "frontend", "index.html")

    @app.get("/<path:asset>")
    def assets(asset):
        # Werkzeug safe_join prevents traversal outside the frontend directory.
        return send_from_directory(ROOT / "frontend", asset)

    app.logger.setLevel(logging.INFO)
    return app
