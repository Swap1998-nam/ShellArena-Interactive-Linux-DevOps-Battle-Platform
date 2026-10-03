"""Offline operator utilities. Stop the app before restoring a backup."""

import argparse
import getpass
import os
from pathlib import Path
import sqlite3
import time
from werkzeug.security import generate_password_hash

parser = argparse.ArgumentParser()
parser.add_argument("--database", default=os.getenv("DATABASE_PATH", "data/shellarena.db"))
sub = parser.add_subparsers(dest="action", required=True)
backup = sub.add_parser("backup")
backup.add_argument("destination")
sub.add_parser("cleanup")
reset = sub.add_parser("reset-password")
reset.add_argument("username")
args = parser.parse_args()
if not Path(args.database).is_file():
    parser.error("Database does not exist.")
with sqlite3.connect(args.database) as db:
    db.execute("PRAGMA foreign_keys=ON")
    if args.action == "backup":
        target = Path(args.destination)
        descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
        with sqlite3.connect(target) as output:
            db.backup(output)
        print(f"Consistent SQLite backup saved to {target}.")
    elif args.action == "cleanup":
        now = int(time.time())
        db.execute("DELETE FROM sessions WHERE expires < ?", (now,))
        db.execute("DELETE FROM rate_limits WHERE expires < ?", (now,))
        removed = db.execute("DELETE FROM users WHERE username IS NULL AND last_seen < ?", (now - 30 * 86400,)).rowcount
        print(f"Removed {removed} inactive guest profiles older than 30 days.")
    elif args.action == "reset-password":
        user = db.execute("SELECT id FROM users WHERE username=?", (args.username,)).fetchone()
        if not user:
            parser.error("Account not found.")
        password = getpass.getpass("New password (at least 12 characters): ")
        if len(password) < 12 or len(password) > 128:
            parser.error("Password must have 12–128 characters.")
        if password != getpass.getpass("Confirm new password: "):
            parser.error("Passwords did not match.")
        db.execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(password), user[0]))
        db.execute("DELETE FROM sessions WHERE user_id=?", (user[0],))
        print("Password reset and all sessions revoked.")
