# Quick Reference Card - Kubernetes & Ansible Deployment

## 🚀 Quick Deploy

```bash
cd ansible && ./deploy.sh
```

## 📋 Essential Commands

### Deployment
```bash
# Deploy with roles
ansible-playbook -i inventory.ini playbook-with-roles.yaml

# Deploy main playbook
ansible-playbook -i inventory.ini playbook.yaml

# Cleanup
ansible-playbook -i inventory.ini cleanup.yaml

# Verify
./verify-deployment.sh
```

### Monitoring
```bash
# Watch pods
kubectl get pods -n bigdata-devops -w

# Check HPA
kubectl get hpa -n bigdata-devops

# Resource usage
kubectl top pods -n bigdata-devops

# Logs
kubectl logs -n bigdata-devops -l app=backend --tail=50
kubectl logs -n bigdata-devops -l app=consumer --tail=50

# Events
kubectl get events -n bigdata-devops --sort-by='.lastTimestamp'
```

### Access Services
```bash
# Frontend
minikube service frontend -n bigdata-devops

# Kibana
minikube service kibana -n bigdata-devops

# Port forward
kubectl port-forward -n bigdata-devops svc/frontend 8501:8501
kubectl port-forward -n bigdata-devops svc/kibana 5601:5601
```

### Scaling
```bash
# Manual scale
kubectl scale deployment backend -n bigdata-devops --replicas=5

# Watch HPA
kubectl get hpa -n bigdata-devops -w
```

### Updates
```bash
# Update image
kubectl set image deployment/backend -n bigdata-devops \
  backend=siddharth194/bigdata-devops:backend-123

# Rollout status
kubectl rollout status deployment/backend -n bigdata-devops

# Rollback
kubectl rollout undo deployment/backend -n bigdata-devops
```

## 🐛 Troubleshooting

```bash
# Pod details
kubectl describe pod <pod-name> -n bigdata-devops

# Init container logs
kubectl logs <pod-name> -n bigdata-devops -c <init-container-name>

# Check service endpoints
kubectl get endpoints -n bigdata-devops

# Check metrics-server
kubectl get pods -n kube-system | grep metrics-server

# Test DB connection
kubectl run -it --rm debug --image=postgres:15 -n bigdata-devops -- \
  psql -h postgres -U postgres -d logindata
```

## 📦 File Locations

```
k8s/                          # All Kubernetes manifests
ansible/playbook-with-roles.yaml    # Main deployment (recommended)
ansible/inventory.ini         # Configuration
ansible/deploy.sh            # Auto-deploy script
ansible/cleanup.yaml         # Cleanup script
```

## ⚙️ Key Components

| Component | Replicas | Port | Type |
|-----------|----------|------|------|
| Frontend | 2-8 (HPA) | 8501 | NodePort |
| Backend | 2-10 (HPA) | 5002 | ClusterIP |
| Consumer | 2-6 (HPA) | - | - |
| Kafka | 1 | 9092 | ClusterIP |
| PostgreSQL | 1 | 5432 | ClusterIP |
| Elasticsearch | 1 | 9200 | ClusterIP |
| Logstash | 1 | 5044 | ClusterIP |
| Kibana | 1 | 5601 | NodePort |

## 🎯 HPA Triggers

- **Backend**: CPU > 70%, Memory > 80%
- **Frontend**: CPU > 70%, Memory > 80%
- **Consumer**: CPU > 75%, Memory > 85%

## 📝 Init Containers

- **Kafka** → runs in KRaft mode (no dependencies)
- **Backend** → waits for Kafka, Logstash
- **Consumer** → waits for Kafka, PostgreSQL, Logstash
- **Frontend** → waits for Backend
- **Logstash** → waits for Elasticsearch
- **Kibana** → waits for Elasticsearch

## 🔐 Secrets

```bash
# View secrets
kubectl get secrets -n bigdata-devops

# Decode secret
kubectl get secret postgres-secret -n bigdata-devops -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
```

## 💾 Persistent Storage

- **PostgreSQL**: 5Gi PVC
- **Elasticsearch**: 10Gi PVC

## 🔧 Environment Variables

```bash
export DOCKER_USERNAME=your_username
export DOCKER_PASSWORD=your_password
export BUILD_NUMBER=123
```

## ✅ Health Check Endpoints

- **Backend**: `GET /health` on port 5002
- **Frontend**: `GET /_stcore/health` on port 8501
- **Elasticsearch**: `GET /_cluster/health` on port 9200
- **Kibana**: `GET /api/status` on port 5601

## 📊 Useful Aliases

Add to `~/.bashrc`:

```bash
alias k='kubectl'
alias kgp='kubectl get pods -n bigdata-devops'
alias kgs='kubectl get svc -n bigdata-devops'
alias kgh='kubectl get hpa -n bigdata-devops'
alias kl='kubectl logs -n bigdata-devops'
alias kd='kubectl describe -n bigdata-devops'
```

## 🎨 Status Indicators

```bash
# All green = healthy
kubectl get pods -n bigdata-devops

# Should see:
# - Running status
# - 1/1, 2/2 ready counts
# - 0 restarts (or low number)
```
