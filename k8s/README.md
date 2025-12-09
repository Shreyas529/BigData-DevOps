# Kubernetes Deployment Guide

## Quick Start

### 1. Prerequisites Setup

```bash
# Install Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start Minikube with adequate resources
minikube start --memory=8192 --cpus=4 --driver=docker

# Install Ansible and dependencies
pip install ansible kubernetes openshift

# Install Ansible Kubernetes collection
ansible-galaxy collection install kubernetes.core
```

### 2. Deploy Using Automated Script

```bash
cd ansible
./deploy.sh
```

### 3. Deploy Using Ansible Directly

```bash
cd ansible

# Using roles (recommended)
ansible-playbook -i inventory.ini playbook-with-roles.yaml

# Or using direct playbook
ansible-playbook -i inventory.ini playbook.yaml
```

## Kubernetes Manifests Overview

### Core Infrastructure

1. **namespace.yaml** - Creates `bigdata-devops` namespace
2. **persistent-volumes.yaml** - PVCs for Postgres and Elasticsearch
3. **secrets.yaml** - Sensitive data (DB credentials, Kafka config)
4. **configmap.yaml** - Application configuration

### Service Deployments

#### Data Layer
- **postgres-deployment.yaml** - PostgreSQL database with health checks
- **db-init-job.yaml** - Kubernetes Job to initialize database schema

#### Messaging Layer
- **zookeeper-deployment.yaml** - Zookeeper for Kafka coordination
- **kafka-deployment.yaml** - Kafka message broker with init containers

#### Logging Stack (ELK)
- **elasticsearch-deployment.yaml** - Log storage with init containers for permissions
- **logstash-deployment.yaml** - Log processing pipeline
- **kibana-deployment.yaml** - Log visualization dashboard

#### Application Layer
- **backend-deployment.yaml** - Flask backend API (2 replicas)
- **consumer-deployment.yaml** - Kafka consumer (2 replicas)
- **frontend-deployment.yaml** - Streamlit frontend (2 replicas)

#### Autoscaling
- **hpa.yaml** - Horizontal Pod Autoscalers for backend, frontend, and consumer

## Key Features Implemented

### 1. Init Containers
Every service has proper init containers to ensure dependencies are ready:

**Example - Backend**:
```yaml
initContainers:
- name: wait-for-kafka
  image: busybox:1.35
  command: ['sh', '-c', 'until nc -z kafka 9092; do echo waiting for kafka; sleep 2; done;']
```

### 2. ConfigMaps
Application configuration separated from code:
- Environment variables
- Logstash pipeline configuration
- ELK settings

### 3. Secrets
Sensitive data properly managed:
- PostgreSQL credentials
- Kafka connection strings
- Docker Hub registry credentials

### 4. Health Checks

**Liveness Probes**: Restart containers if they become unhealthy
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 5002
  initialDelaySeconds: 30
  periodSeconds: 10
```

**Readiness Probes**: Don't send traffic until ready
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 5002
  initialDelaySeconds: 15
  periodSeconds: 5
```

### 5. Resource Management
Every container has resource requests and limits:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 6. Horizontal Pod Autoscaling
Automatic scaling based on CPU and memory:
```yaml
spec:
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Ansible Roles Structure

```
ansible/roles/kubernetes-deploy/
├── defaults/main.yml          # Default variables
├── meta/main.yml              # Role metadata
└── tasks/
    ├── main.yml              # Orchestrates all tasks
    ├── prerequisites.yml     # Setup Minikube
    ├── config.yml           # Deploy ConfigMaps/Secrets
    ├── messaging.yml        # Deploy Kafka/Zookeeper
    ├── database.yml         # Deploy PostgreSQL
    ├── elk.yml              # Deploy ELK Stack
    ├── application.yml      # Deploy app services
    └── get_urls.yml         # Get service URLs
```

## Deployment Flow

```
1. Prerequisites Check
   └─> Verify Minikube running
   └─> Enable metrics-server

2. Configuration Setup
   └─> Create namespace
   └─> Deploy PVCs
   └─> Deploy ConfigMaps
   └─> Deploy Secrets

3. Infrastructure Layer
   └─> Zookeeper
   └─> Kafka (waits for Zookeeper)
   └─> PostgreSQL
   └─> DB Init Job (waits for PostgreSQL)

4. Logging Stack
   └─> Elasticsearch (with init containers)
   └─> Logstash (waits for Elasticsearch)
   └─> Kibana (waits for Elasticsearch)

5. Application Layer
   └─> Backend (waits for Kafka, Logstash)
   └─> Consumer (waits for Kafka, PostgreSQL, Logstash)
   └─> Frontend (waits for Backend)

6. Autoscaling
   └─> Deploy HPA for all app services
```

## Accessing Services

### Using Minikube Service Command
```bash
# Frontend
minikube service frontend -n bigdata-devops

# Kibana
minikube service kibana -n bigdata-devops
```

### Using Port Forwarding
```bash
# Frontend
kubectl port-forward -n bigdata-devops svc/frontend 8501:8501

# Backend
kubectl port-forward -n bigdata-devops svc/backend 5002:5002

# Kibana
kubectl port-forward -n bigdata-devops svc/kibana 5601:5601
```

## Monitoring Commands

```bash
# Watch all pods
kubectl get pods -n bigdata-devops -w

# Check HPA status
kubectl get hpa -n bigdata-devops

# View resource usage
kubectl top pods -n bigdata-devops
kubectl top nodes

# Check logs
kubectl logs -n bigdata-devops -l app=backend --tail=50
kubectl logs -n bigdata-devops -l app=consumer --tail=50

# Describe a pod (useful for debugging)
kubectl describe pod <pod-name> -n bigdata-devops

# Check events
kubectl get events -n bigdata-devops --sort-by='.lastTimestamp'
```

## Scaling

### Manual Scaling
```bash
# Scale backend
kubectl scale deployment backend -n bigdata-devops --replicas=5

# Scale frontend
kubectl scale deployment frontend -n bigdata-devops --replicas=3
```

### HPA will automatically scale based on load
```bash
# Monitor HPA decisions
kubectl get hpa -n bigdata-devops -w
```

## Rolling Updates

When new images are pushed to Docker Hub:

```bash
# Update backend image
kubectl set image deployment/backend -n bigdata-devops \
  backend=siddharth194/bigdata-devops:backend-123

# Check rollout status
kubectl rollout status deployment/backend -n bigdata-devops

# Rollback if needed
kubectl rollout undo deployment/backend -n bigdata-devops
```

## Troubleshooting

### Pod Stuck in Pending
```bash
kubectl describe pod <pod-name> -n bigdata-devops
# Check for: insufficient resources, PVC issues, image pull errors
```

### Init Container Failing
```bash
kubectl logs <pod-name> -n bigdata-devops -c <init-container-name>
```

### Service Not Accessible
```bash
kubectl get svc -n bigdata-devops
kubectl get endpoints -n bigdata-devops
```

### HPA Not Scaling
```bash
# Check metrics-server
kubectl get pods -n kube-system | grep metrics-server

# Check if metrics are available
kubectl top pods -n bigdata-devops
```

### Database Connection Issues
```bash
# Check if postgres is ready
kubectl get pods -n bigdata-devops -l app=postgres

# Check logs
kubectl logs -n bigdata-devops -l app=postgres

# Test connection from a pod
kubectl run -it --rm debug --image=postgres:15 --restart=Never -n bigdata-devops -- \
  psql -h postgres -U postgres -d logindata
```

## Cleanup

### Remove entire deployment
```bash
cd ansible
ansible-playbook -i inventory.ini cleanup.yaml
```

### Or manually
```bash
kubectl delete namespace bigdata-devops
```

## Environment Variables

The deployment can be customized via environment variables:

```bash
export DOCKER_USERNAME=your_username
export DOCKER_PASSWORD=your_password
export BUILD_NUMBER=123

cd ansible
ansible-playbook -i inventory.ini playbook-with-roles.yaml
```

## Best Practices Implemented

✅ **Init Containers** - Proper dependency management
✅ **Health Checks** - Liveness and readiness probes
✅ **Resource Limits** - Prevent resource starvation
✅ **ConfigMaps** - Externalized configuration
✅ **Secrets** - Secure credential management
✅ **HPA** - Automatic horizontal scaling
✅ **Rolling Updates** - Zero-downtime deployments
✅ **Persistent Storage** - Data persistence with PVCs
✅ **Namespaces** - Resource isolation
✅ **Service Discovery** - DNS-based service resolution
✅ **Modular Ansible Roles** - Reusable deployment code
