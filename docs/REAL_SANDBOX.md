# Real Linux execution is a separate trust boundary

The original prototype mounted `/var/run/docker.sock` into the web backend and created a container for each incoming command. This gave the web process broad control over the host daemon and did not provide persistent terminal state or a complete tenant-isolation design.

The default application now uses a simulator. Its Docker and Kubernetes missions teach command structure and troubleshooting against fixed snapshots; they do not manage real infrastructure. This change is deliberate and visible in the UI.

`backend/docker_manager.py` retains a **standalone local CLI helper**, disabled unless `SHELLARENA_LOCAL_LAB=1`. It is never imported by the Flask application. It provides a short-lived, network-disabled, non-root, read-only-root container with CPU, memory, process, log, and execution-time limits. Each call is stateless and removes the container afterward. It is not a PTY, persistent session, or remotely accessible service.

For your own practice on a disposable VM with a properly configured rootless Docker daemon:

```bash
docker build -f docker/sandbox.Dockerfile -t shellarena-sandbox:local .
.venv/bin/pip install -r backend/requirements-lab.txt
SHELLARENA_LOCAL_LAB=1 .venv/bin/python -c 'from backend.docker_manager import execute_command; print(execute_command("pwd && whoami && ls"))'
```

This path was not executed in the build workspace because no Docker daemon was available. Verify resource enforcement in your VM; rootless cgroup support depends on the host. Even restricted containers share a kernel. Do not expose this helper to untrusted public commands.

A future public Linux arena needs a separate authenticated runner API, bounded session allocation, idle/absolute TTL cleanup, reliable process cancellation, output backpressure, per-tenant isolation such as microVMs or an appropriately reviewed sandbox runtime, no cloud credentials/metadata access, deny-by-default network policy, host hardening, abuse controls, and adversarial isolation tests. Design and review that service separately before wiring it into the learning app.
