"""Offline, single-user Docker practice runner. Never imported by the web API.

Use only on a disposable development VM with a rootless Docker daemon.
This is not a multi-tenant sandbox service or a production isolation boundary.
"""

import os
import docker


# Isolated container tmpfs target; never a host temporary file.
CONTAINER_TMP = "/tmp"  # nosec B108


def execute_command(command):
    if not isinstance(command, str) or not command.strip() or len(command) > 512:
        raise ValueError("A command of 1–512 characters is required.")
    if os.environ.get("SHELLARENA_LOCAL_LAB") != "1":
        raise RuntimeError("This runner is disabled. See docs/REAL_SANDBOX.md.")
    client = docker.from_env(timeout=15)
    container = None
    try:
        container = client.containers.run(
            "shellarena-sandbox:local",
            command=["timeout", "-s", "KILL", "8", "sh", "-c", command],
            detach=True,
            network_disabled=True,
            read_only=True,
            user="10001:10001",
            cap_drop=["ALL"],
            security_opt=["no-new-privileges:true"],
            mem_limit="128m",
            memswap_limit="128m",
            nano_cpus=500_000_000,
            pids_limit=32,
            tmpfs={
                CONTAINER_TMP: "rw,noexec,nosuid,size=16m,uid=10001,gid=10001",
                "/workspace": "rw,noexec,nosuid,size=16m,uid=10001,gid=10001",
            },
            working_dir="/workspace",
            log_config=docker.types.LogConfig(type="local", config={"max-size": "64k", "max-file": "1"}),
        )
        container.wait(timeout=12)
        return container.logs(tail=200).decode("utf-8", errors="replace")[:32768]
    finally:
        if container is not None:
            container.remove(force=True)
        client.close()
