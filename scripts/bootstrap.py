"""Generate local configuration without displaying secret values."""

import os
from pathlib import Path
import secrets

root = Path(__file__).resolve().parent.parent
path = root / ".env"
try:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    print(".env already exists; existing values kept.")
else:
    with os.fdopen(descriptor, "w") as stream:
        stream.write(
            f"SECRET_KEY={secrets.token_hex(32)}\nMETRICS_TOKEN={secrets.token_hex(32)}\nAPP_DOMAIN=shellarena.example.com\n"
        )
    print("Created .env with fresh keys. Keep this file private and out of Git.")
