# Ansible Requirements for Kubernetes Deployment

This directory contains Ansible playbooks and roles for deploying the BigData-DevOps application to Minikube.

## Prerequisites

1. **Install Ansible**:
```bash
pip install ansible
```

2. **Install Kubernetes Ansible Collection**:
```bash
ansible-galaxy collection install kubernetes.core
```

3. **Install Python dependencies**:
```bash
pip install kubernetes openshift
```

4. **Ensure Minikube is installed and running**:
```bash
minikube start --memory=8192 --cpus=4
```

5. **Configure kubectl**:
```bash
kubectl config use-context minikube
```

## File Structure

```
ansible/
├── inventory.ini                    # Inventory configuration
├── playbook.yaml                    # Main playbook (direct tasks)
├── playbook-with-roles.yaml         # Playbook using roles (recommended)
└── roles/
    └── kubernetes-deploy/
        ├── defaults/
        │   └── main.yml            # Default variables
        ├── meta/
        │   └── main.yml            # Role metadata
        └── tasks/
            ├── main.yml            # Main task file
            ├── prerequisites.yml   # Minikube setup
            ├── config.yml          # ConfigMaps and Secrets
            ├── messaging.yml       # Kafka (KRaft mode)
            ├── database.yml        # PostgreSQL setup
            ├── elk.yml             # ELK Stack deployment
            ├── application.yml     # App services deployment
            └── get_urls.yml        # Get service URLs
```

## Usage

### Option 1: Using the main playbook (all tasks in one file)
```bash
cd ansible
ansible-playbook -i inventory.ini playbook.yaml
```

### Option 2: Using roles (modular approach - recommended)
```bash
cd ansible
ansible-playbook -i inventory.ini playbook-with-roles.yaml
```

### With Docker Hub credentials (for pulling private images)
```bash
export DOCKER_USERNAME=your_username
export DOCKER_PASSWORD=your_password
export BUILD_NUMBER=123

cd ansible
ansible-playbook -i inventory.ini playbook-with-roles.yaml
```

### Run specific tags
```bash
ansible-playbook -i inventory.ini playbook.yaml --tags "config,database"
```

## Environment Variables

- `DOCKER_USERNAME`: Docker Hub username (default: siddharth194)
- `DOCKER_PASSWORD`: Docker Hub password (default: empty)
- `BUILD_NUMBER`: Build number for image tags (default: latest)

## Deployment Order

The playbook deploys services in the following order:

1. **Prerequisites**: Verify Minikube, enable metrics-server
2. **Configuration**: Create namespace, PVCs, ConfigMaps, Secrets
3. **Messaging**: Deploy Kafka (KRaft mode)
4. **Database**: Deploy PostgreSQL → Run DB init job
5. **ELK Stack**: Deploy Elasticsearch → Logstash → Kibana
6. **Application**: Deploy Backend → Consumer → Frontend
7. **Autoscaling**: Deploy HPA configurations

## Checking Deployment Status

```bash
# Check all pods
kubectl get pods -n bigdata-devops

# Check services
kubectl get svc -n bigdata-devops

# Check HPA status
kubectl get hpa -n bigdata-devops

# Check logs
kubectl logs -n bigdata-devops <pod-name>

# Get service URLs
minikube service frontend -n bigdata-devops --url
minikube service kibana -n bigdata-devops --url
```

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod <pod-name> -n bigdata-devops
kubectl logs <pod-name> -n bigdata-devops
```

### Init container issues
```bash
kubectl logs <pod-name> -n bigdata-devops -c <init-container-name>
```

### Service not accessible
```bash
kubectl get svc -n bigdata-devops
minikube service list -n bigdata-devops
```

### HPA not working
```bash
# Check if metrics-server is running
kubectl get pods -n kube-system | grep metrics-server

# Check metrics availability
kubectl top nodes
kubectl top pods -n bigdata-devops
```

## Clean Up

To remove all deployed resources:

```bash
kubectl delete namespace bigdata-devops
```

Or use the cleanup playbook:

```bash
ansible-playbook -i inventory.ini cleanup.yaml
```

#### change to trigger pipeline
