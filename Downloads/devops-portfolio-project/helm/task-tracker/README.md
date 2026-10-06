# task-tracker Helm chart

Packages the app + MongoDB deployment that previously lived as plain YAML in
`k8s/*.yaml` into one templated, versioned, installable release — including
the two fixes discovered while debugging on `kind`:
- `mongo.readinessProbe.timeoutSeconds: 10` (default `mongosh` startup
  takes longer than Kubernetes' default 1s probe timeout)
- `strategy: Recreate` on the mongo Deployment (prevents two pods from
  fighting over the same data volume during a rollout)

## Install

```bash
# from the devops-portfolio-project root
helm install task-tracker ./helm/task-tracker
```

This creates everything, including the `task-tracker` namespace.

## Upgrade (after changing values.yaml or templates)

```bash
helm upgrade task-tracker ./helm/task-tracker
```

## Override a value without editing the file

```bash
helm upgrade task-tracker ./helm/task-tracker --set app.replicaCount=3
```

## Uninstall

```bash
helm uninstall task-tracker
```

Note: this does NOT delete the `mongo-data` PVC by default — delete it
separately if you want a truly clean slate:
```bash
kubectl delete pvc mongo-data -n task-tracker
```

## See what would be generated, without installing anything

```bash
helm template task-tracker ./helm/task-tracker
```
Useful for sanity-checking the YAML before it ever touches the cluster.
