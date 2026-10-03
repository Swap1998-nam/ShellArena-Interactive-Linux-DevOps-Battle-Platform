# Deployment

## Local practice

The supported build is the root `Dockerfile`. The old split frontend/backend Dockerfiles are removed. The web UI and API now share port 8000 in the container and port 3000 on the host through Compose. No npm build is required for the app.

```bash
python3 scripts/bootstrap.py
docker compose up --build -d
curl --fail http://127.0.0.1:3000/health/ready
```

## Single-host HTTPS beta

1. Use a dedicated host and persistent storage. Generate `.env` and change `APP_DOMAIN` to the real hostname. Store `.env` outside source control with restrictive permissions.
2. Configure your HTTPS reverse proxy with a valid certificate, preserve the public Host header, and forward only to `127.0.0.1:3000`. Route to the application on the same host. Keep the application port closed to public ingress.
3. Start production mode:

```bash
docker compose -f docker-compose.yml -f compose.production.yml up --build -d
```

4. Access through `https://YOUR_DOMAIN`. Production cookies are Secure and will not work over plain HTTP. `PUBLIC_ORIGIN` must exactly match the browser origin.
5. Verify readiness, sign-up/sign-in, command completion, reboot persistence, backup restore, and HTTPS headers. Protect `/metrics` at the gateway as well as with its bearer token.

Do not set development mode to bypass cookie or trusted-host failures. Fix hostname/TLS configuration instead. HSTS is sent only in production; ensure HTTPS is working before onboarding users.

## Kubernetes templates

These are reviewable deployment templates, not manifests already verified in your cluster. They require:

- A registry image built and scanned by your pipeline.
- A default StorageClass supporting the PVC. On EKS, configure your storage driver and its AWS permissions first.
- An ingress-nginx controller in namespace `ingress-nginx` and a valid `shellarena-tls` Secret in namespace `shellarena`.
- A CNI that enforces NetworkPolicy.
- A `shellarena-secrets` Secret with `SECRET_KEY` and `METRICS_TOKEN`.

Edit the hostname in `application.yml` and `ingress.yml`. Replace the image placeholder, preferably with `registry/repository@sha256:...` from the tested build. Do not deploy a mutable `latest` tag.

```bash
kubectl apply -f deploy/kubernetes/namespace.yml
# Create shellarena-secrets using your secret-management workflow.
# Create shellarena-tls using your certificate-management workflow.
kubectl apply -f deploy/kubernetes/application.yml
kubectl apply -f deploy/kubernetes/ingress.yml
kubectl apply -f deploy/kubernetes/network-policy.yml
kubectl -n shellarena rollout status deployment/shellarena --timeout=180s
kubectl -n shellarena get pods,pvc,service,ingress
```

The image runs as UID/GID 10001, with a read-only root filesystem, bounded writable `/tmp`, persistent `/app/data`, no capabilities, no service-account token, and the runtime default seccomp profile. Keep **one replica** and the **Recreate** strategy. SQLite must not be scaled by increasing replicas or adding an HPA. Deployments have brief downtime; schedule updates accordingly.

The ingress example is for ingress-nginx. An AWS Load Balancer Controller/ALB setup requires its own ingress class, annotations, certificate, target health checks, and network rules. Do not apply the nginx-only policy to an ALB deployment unchanged. This release does not provision EKS, ALB, IAM, DNS, certificates, or databases.

If scraping metrics from another namespace, explicitly allow that Prometheus source in NetworkPolicy and configure its bearer token and Host header. Egress is denied because this simulator does not need external network access.

## Release and rollback

Build from a reviewed commit, pass CI, scan the image, record its digest, back up the database, then update the deployment image. Verify readiness and account/mission smoke tests after rollout. For a code-only rollback with unchanged schema, redeploy the previous tested digest. If a future release changes schema, use its migration/rollback plan; do not assume downgrading code is safe for the new database.
