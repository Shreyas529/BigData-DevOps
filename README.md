# BigData-DevOps

# BigData-DevOps

A complete CI/CD pipeline implementation for a distributed login event processing system with real-time analytics, automated deployment, and comprehensive monitoring.

## Overview

This project demonstrates a production-grade DevOps implementation featuring:
- Real-time login event processing using Kafka
- PostgreSQL for data persistence
- ELK Stack (Elasticsearch, Logstash, Kibana) for centralized logging
- Kubernetes deployment with Horizontal Pod Autoscaling
- Ansible automation for infrastructure management
- Jenkins CI/CD pipeline with automated testing and deployment

## Architecture

### Application Components

- **Frontend**: Streamlit-based login interface
- **Backend**: Flask API for event generation and processing
- **Consumer**: Kafka consumer for event ingestion into PostgreSQL
- **Analytics Dashboard**: Real-time analytics dashboard
- **Message Queue**: Kafka (KRaft mode, no Zookeeper required)
- **Database**: PostgreSQL with persistent storage
- **Logging**: ELK Stack for centralized log management

### Infrastructure

- **Container Orchestration**: Kubernetes on Minikube
- **Configuration Management**: Ansible with modular roles
- **CI/CD**: Jenkins with automated testing and deployment
- **Container Registry**: Docker Hub
- **Secrets Management**: HashiCorp Vault (dev mode)

## Prerequisites

### Software Requirements

```bash
# Docker
docker --version  # 20.10+

# Docker Compose
docker-compose --version  # 1.29+

# Minikube
minikube version  # 1.25+

# Kubectl
kubectl version --client  # 1.23+

# Ansible
ansible --version  # 2.12+
pip install kubernetes openshift

# Python
python --version  # 3.10+
```

### Ansible Collections

```bash
ansible-galaxy collection install kubernetes.core
ansible-galaxy install -r ansible/requirements.yml
```

## Quick Start

### Local Development with Docker Compose

```bash
# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:8501
# Backend: http://localhost:5002
# Kibana: http://localhost:5601
```

### Production Deployment to Kubernetes

#### Manual Ansible Deployment

```bash
# Start Minikube
minikube start --memory=8192 --cpus=4 --driver=docker

# Deploy using Ansible roles
cd ansible
ansible-playbook -i inventory.ini playbook-with-roles.yaml

# Get service URLs
minikube service frontend -n bigdata-devops --url
minikube service kibana -n bigdata-devops --url
```

## CI/CD Pipeline

### Jenkins Setup

1. Install Jenkins with required plugins:
   - Docker Pipeline
   - Kubernetes
   - GitHub
   - Ansible

2. Configure credentials in Jenkins:
   - Docker Hub: `dockerhub-credentials`
   - GitHub: `github-credentials`

3. Create pipeline job pointing to `jenkins/Jenkinsfile`

4. Configure GitHub webhook for automatic triggers

### Pipeline Stages

```
Git Push → Cleanup → Checkout → Tests → Build Images → 
Push to DockerHub → Update K8s Manifests → Deploy via Ansible → Verify
```

### Manual Trigger

```bash
# From Jenkins UI: Build Now
# Or commit and push changes
git add .
git commit -m "Update feature"
git push origin main
```

## Testing

### Run Automated Tests

```bash
# Using Docker Compose
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Direct pytest
cd tests
pytest -v
```

### Test Coverage

- Event generation and validation
- Database operations
- Kafka producer/consumer
- API endpoints
- Window-based analytics

## Monitoring and Operations

### Check Deployment Status

```bash
# All pods
kubectl get pods -n bigdata-devops

# Services
kubectl get svc -n bigdata-devops

# HPA status
kubectl get hpa -n bigdata-devops

# Resource usage
kubectl top pods -n bigdata-devops
```

### View Logs

```bash
# Application logs
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

# Port forwarding
kubectl port-forward -n bigdata-devops svc/frontend 8501:8501
kubectl port-forward -n bigdata-devops svc/kibana 5601:5601
```

## Scaling

### Manual Scaling

```bash
# Scale backend pods
kubectl scale deployment backend -n bigdata-devops --replicas=5

# Scale frontend pods
kubectl scale deployment frontend -n bigdata-devops --replicas=3
```

### Horizontal Pod Autoscaling

HPA is automatically configured for:
- Backend: 2-10 pods (CPU 70%, Memory 80%)
- Frontend: 2-8 pods (CPU 70%, Memory 80%)
- Consumer: 2-6 pods (CPU 75%, Memory 85%)

Monitor autoscaling:
```bash
kubectl get hpa -n bigdata-devops -w
```

## Configuration

### Environment Variables

```bash
# Deployment configuration
export DOCKER_USERNAME=your_username
export DOCKER_PASSWORD=your_password
export BUILD_NUMBER=123

# Application configuration
export KAFKA_BOOTSTRAP_SERVERS=kafka:9092
export POSTGRES_HOST=postgres
export POSTGRES_DB=logindata
```

### Ansible Variables

Edit [`ansible/inventory.ini`](ansible/inventory.ini):
```ini
[minikube]
localhost ansible_connection=local

[minikube:vars]
k8s_namespace=bigdata-devops
docker_registry=siddharth194
backend_replicas=2
frontend_replicas=2
```

## Cleanup

### Remove Deployment

```bash
# Using Ansible
cd ansible
ansible-playbook -i inventory.ini cleanup.yaml

# Or delete namespace
kubectl delete namespace bigdata-devops
```

### Stop Minikube

```bash
minikube stop
minikube delete
```

## Project Structure

```
BigData-DevOps/
├── backend/               # Flask backend and Kafka consumer
├── frontend/              # Streamlit frontend
├── k8s/                   # Kubernetes manifests
├── ansible/               # Ansible playbooks and roles
├── jenkins/               # Jenkins pipeline configuration
├── tests/                 # Automated tests
├── elk/                   # Logstash configuration
├── docker-compose.yml     # Local development setup
└── docker-compose.test.yml # Test environment
```



## DevOps Best Practices

- Infrastructure as Code (Ansible, Kubernetes)
- Containerization (Docker)
- Automated CI/CD (Jenkins)
- Automated Testing (pytest)
- Centralized Logging (ELK Stack)
- Secrets Management (Vault)
- Health Checks and Probes
- Resource Limits and Requests
- Horizontal Pod Autoscaling
- Rolling Updates with Zero Downtime
- Persistent Storage (PVCs)

## Technologies Used

- **Languages**: Python
- **Frameworks**: Flask, Streamlit
- **Message Queue**: Apache Kafka
- **Database**: PostgreSQL
- **Logging**: Elasticsearch, Logstash, Kibana
- **Container**: Docker, Docker Compose
- **Orchestration**: Kubernetes, Minikube
- **Automation**: Ansible
- **CI/CD**: Jenkins
- **Secrets**: HashiCorp Vault
- **Testing**: pytest, asyncpg
