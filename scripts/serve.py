"""Start the local WSGI server using values from the generated .env file."""

import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
os.chdir(root)
if not (root / ".env").exists():
    subprocess.run([sys.executable, "scripts/bootstrap.py"], check=True)
for line in (root / ".env").read_text().splitlines():
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)
os.execv(sys.executable, [sys.executable, "-m", "gunicorn", "--config", "gunicorn.conf.py", "backend.wsgi:app"])
