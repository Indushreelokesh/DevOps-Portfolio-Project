# Task Tracker — DevOps Portfolio Project

A deliberately simple Flask + MongoDB CRUD API, used as the vehicle for a full
DevOps pipeline: Docker → Jenkins CI/CD → Kubernetes → (next) Terraform/EKS →
monitoring. The app itself isn't the point — the automation and infra around
it are.

## Architecture (current stage: local)

```
Jenkins ── lint/test/build ──▶ Docker image ──▶ kind cluster
                                                    │
                                        Deployment (task-tracker, 2 replicas)
                                                    │
                                              Service ── Ingress
                                                    │
                                        Deployment (mongo, 1 replica + PVC)
```

## Run it locally with Docker Compose (fastest way to see it working)

```bash
docker compose up --build
curl http://localhost:5000/health
curl -X POST http://localhost:5000/tasks -H "Content-Type: application/json" \
     -d '{"title":"Set up kind cluster"}'
curl http://localhost:5000/tasks
```

## Run the test suite

```bash
cd app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -v
```
Tests use `mongomock`, so no real database is needed to run them — this is
what lets Jenkins run them in seconds on every commit.

## Run it on a local Kubernetes cluster (kind)

1. Install [kind](https://kind.sigs.k8s.io/) and `kubectl`.
2. Create a cluster and load the image into it (kind can't pull from your
   local Docker daemon otherwise):
   ```bash
   kind create cluster --name devops-portfolio
   docker build -t task-tracker:local .
   kind load docker-image task-tracker:local --name devops-portfolio
   ```
3. Apply the manifests in order:
   ```bash
   kubectl apply -f k8s/00-namespace.yaml
   kubectl apply -f k8s/10-mongo.yaml
   kubectl apply -f k8s/20-configmap.yaml
   kubectl apply -f k8s/30-app.yaml
   ```
4. Check it's healthy:
   ```bash
   kubectl -n task-tracker get pods
   kubectl -n task-tracker port-forward svc/task-tracker 8080:80
   curl http://localhost:8080/health
   ```
5. (Optional) install an ingress controller and apply `k8s/40-ingress.yaml`
   to reach it via `http://task-tracker.local` instead of port-forwarding.

## Run the Jenkins pipeline

1. Run Jenkins locally (simplest: `docker run -p 8080:8080 -p 50000:50000 -v jenkins_home:/var/jenkins_home -v /var/run/docker.sock:/var/run/docker.sock jenkins/jenkins:lts`).
2. Install the Docker Pipeline and JUnit plugins.
3. Add a "dockerhub-creds" credential (Username/Password) if you want the
   push/deploy stages to run — otherwise they'll just be skipped on
   non-`main` branches, and you can comment them out while learning.
4. Create a Pipeline job pointing at this repo's `Jenkinsfile`.
5. Trigger a build and watch each stage: lint → test → build → scan → push → deploy.

## What's intentionally deferred to later weeks

- **Helm chart** (wraps `k8s/*.yaml` into a templated, versioned release) — Week 2, day 14.
- **Terraform + EKS** (this exact app, but on real AWS infra) — Week 3.
- **ArgoCD GitOps** (cluster state driven from a manifests repo, not `kubectl apply`) — Week 3, day 19.
- **Prometheus/Grafana** (the app already exposes `/metrics` via
  `prometheus-flask-exporter`, ready to be scraped) — Week 4.
- **Secrets Manager instead of the plain ConfigMap** — once real AWS creds exist.

## Interview talking points this project already gives you

- Multi-stage Docker build and *why* it shrinks the final image.
- Liveness vs. readiness probes — `/health` vs `/ready` are deliberately
  different endpoints, which is a real interview question.
- Why tests use `mongomock` instead of a real database in CI.
- HPA scaling on CPU, and what you'd change to scale on custom metrics instead.
- Non-root container user and why that matters for security.
