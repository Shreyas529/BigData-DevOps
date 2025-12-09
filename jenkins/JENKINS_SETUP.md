# Jenkins CI/CD Pipeline Setup Guide

## Overview

The Jenkins pipeline now includes complete CI/CD automation with Ansible deployment to Minikube. The pipeline automatically triggers on Git push and deploys the application.

## Pipeline Stages

1. **Cleanup Previous** - Remove old Docker images and containers
2. **Checkout** - Pull latest code from GitHub
3. **Run Tests** - Execute automated tests
4. **Build Images** - Build Docker images for backend and frontend
5. **Push to DockerHub** - Push images with build number tags
6. **Pull Images from DockerHub** - Verify image availability
7. **Update Kubernetes Manifests** - Update image tags in K8s manifests
8. **Deploy to Minikube via Ansible** - Deploy using Ansible playbook
9. **Verify Deployment** - Check deployment status and get service URLs

## Prerequisites

### 1. Jenkins Installation

```bash
# Install Jenkins (Ubuntu/Debian)
wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io.key | sudo apt-key add -
sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
sudo apt update
sudo apt install jenkins

# Start Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
```

Access Jenkins at: `http://localhost:8080`

### 2. Jenkins Plugins Required

Install these plugins via **Manage Jenkins → Manage Plugins**:

- **Git Plugin** - For GitHub integration
- **GitHub Plugin** - For webhooks
- **Docker Pipeline** - For Docker operations
- **Pipeline** - For pipeline support
- **Credentials Binding** - For secure credential handling
- **Kubernetes CLI Plugin** (optional) - For kubectl commands

### 3. Jenkins System Configuration

#### Install Required Tools on Jenkins Server

```bash
# Docker
sudo apt install docker.io
sudo usermod -aG docker jenkins

# Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install kubectl /usr/local/bin/kubectl

# Python & pip
sudo apt install python3 python3-pip

# Ansible
pip3 install ansible

# Restart Jenkins
sudo systemctl restart jenkins
```

### 4. Configure Jenkins Credentials

Go to **Manage Jenkins → Manage Credentials → Global → Add Credentials**

#### a) Docker Hub Credentials
- **Kind**: Username with password
- **ID**: `dockerhub-credentials`
- **Username**: Your Docker Hub username
- **Password**: Your Docker Hub password or access token
- **Description**: Docker Hub Credentials

#### b) GitHub Credentials
- **Kind**: Username with password (or GitHub Personal Access Token)
- **ID**: `github-credentials`
- **Username**: Your GitHub username
- **Password**: Your GitHub Personal Access Token
- **Description**: GitHub Credentials

To create GitHub token:
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` permissions
3. Copy and use as password

## Setting Up the Pipeline

### Method 1: Pipeline from SCM (Recommended)

1. **Create New Item**
   - Click "New Item"
   - Enter name: `BigData-DevOps-Pipeline`
   - Select "Pipeline"
   - Click OK

2. **Configure Pipeline**
   - **General**:
     - ✅ Check "GitHub project"
     - Project url: `https://github.com/Shreyas529/BigData-DevOps/`
   
   - **Build Triggers**:
     - ✅ Check "GitHub hook trigger for GITScm polling"
     - ✅ Check "Poll SCM" and enter: `H/5 * * * *` (polls every 5 minutes)
   
   - **Pipeline**:
     - Definition: **Pipeline script from SCM**
     - SCM: **Git**
     - Repository URL: `https://github.com/Shreyas529/BigData-DevOps.git`
     - Credentials: Select `github-credentials`
     - Branch: `*/main`
     - Script Path: `jenkins/Jenkinsfile`

3. **Save**

### Method 2: Pipeline Script (Alternative)

Copy the entire Jenkinsfile content directly into the Pipeline script section.

## GitHub Webhook Configuration

### Option 1: GitHub Webhook (Recommended - Instant Trigger)

1. **In GitHub Repository**:
   - Go to your repo: `https://github.com/Shreyas529/BigData-DevOps`
   - Settings → Webhooks → Add webhook
   
2. **Configure Webhook**:
   - **Payload URL**: `http://YOUR_JENKINS_URL/github-webhook/`
     - Example: `http://jenkins.example.com:8080/github-webhook/`
   - **Content type**: `application/json`
   - **Secret**: Leave empty (or set one for security)
   - **Which events**: Just the push event
   - ✅ Active
   
3. **Save**

### Option 2: Poll SCM (Fallback - 5 Minute Delay)

Already configured in Jenkinsfile:
```groovy
triggers {
    pollSCM('H/5 * * * *')
}
```

## Minikube Setup on Jenkins Server

```bash
# Start Minikube (as jenkins user)
sudo su - jenkins
minikube start --memory=8192 --cpus=4 --driver=docker

# Enable metrics-server for HPA
minikube addons enable metrics-server

# Verify
minikube status
kubectl get nodes
```

## Environment Variables

The pipeline uses these environment variables:

```groovy
environment {
    DOCKER_HUB_CREDENTIALS = 'dockerhub-credentials'
    IMAGE_NAME = 'siddharth194/bigdata-devops'
    BACKEND_TAG = 'backend'
    FRONTEND_TAG = 'frontend'
}
```

Update `IMAGE_NAME` to match your Docker Hub username.

## Pipeline Workflow

```
[Git Push] 
    ↓
[GitHub Webhook Triggers Jenkins]
    ↓
[Cleanup Previous Build Artifacts]
    ↓
[Checkout Code from GitHub]
    ↓
[Run Automated Tests]
    ↓
[Build Docker Images]
    ├─ backend:backend-<BUILD_NUMBER>
    └─ frontend:frontend-<BUILD_NUMBER>
    ↓
[Push Images to DockerHub]
    ↓
[Pull Images (Verification)]
    ↓
[Update K8s Manifests with New Tags]
    ↓
[Deploy via Ansible to Minikube]
    ├─ Install Ansible dependencies
    ├─ Run playbook-with-roles.yaml
    └─ Deploy all services
    ↓
[Verify Deployment]
    ├─ Check pod status
    ├─ Check services
    └─ Get service URLs
    ↓
[Success/Failure Notification]
```

## Testing the Pipeline

### 1. Manual Trigger

- Go to Jenkins → Your Pipeline
- Click "Build Now"
- Watch the console output

### 2. Git Push Trigger

```bash
# Make a change
echo "# Test change" >> README.md
git add README.md
git commit -m "Test Jenkins pipeline"
git push origin main

# Jenkins should automatically trigger within 5 minutes (or instantly with webhook)
```

## Monitoring the Pipeline

### Jenkins Console Output

1. Click on the running build number
2. Click "Console Output"
3. Watch real-time logs

### Check Deployment

```bash
# After successful deployment
kubectl get pods -n bigdata-devops
kubectl get svc -n bigdata-devops
kubectl get hpa -n bigdata-devops

# Get service URLs
minikube service frontend -n bigdata-devops --url
minikube service kibana -n bigdata-devops --url
```

## Troubleshooting

### Issue: Jenkins can't connect to Docker

```bash
# Add jenkins user to docker group
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

### Issue: Minikube not accessible

```bash
# Check Minikube status
sudo su - jenkins
minikube status

# If not running, start it
minikube start --memory=8192 --cpus=4
```

### Issue: Ansible not found

```bash
# Install Ansible
sudo pip3 install ansible
ansible --version
```

### Issue: Kubernetes collection missing

```bash
ansible-galaxy collection install kubernetes.core
pip3 install kubernetes openshift
```

### Issue: Permission denied for kubectl

```bash
# Set proper permissions
sudo chown -R jenkins:jenkins /home/jenkins/.kube
sudo chown -R jenkins:jenkins /home/jenkins/.minikube
```

### Issue: Image pull errors

Check Docker Hub credentials:
- Verify credentials in Jenkins
- Test login: `docker login -u <username>`
- Ensure images are public or credentials are correct

## Pipeline Features

### ✅ Automated Testing
- Runs tests before deployment
- Fails pipeline if tests fail

### ✅ Docker Image Versioning
- Images tagged with BUILD_NUMBER
- Easy rollback to previous versions

### ✅ Zero-Downtime Deployment
- Rolling updates configured in K8s
- Health checks ensure smooth transitions

### ✅ Auto-Scaling
- HPA automatically scales based on load
- Configured in hpa.yaml

### ✅ Deployment Verification
- Automatic verification after deployment
- Service URLs displayed in console

### ✅ Rollback Capability
- Previous images remain in DockerHub
- Easy rollback via kubectl or Jenkins

## Rollback Procedure

If deployment fails or has issues:

```bash
# Option 1: Via kubectl
kubectl rollout undo deployment/backend -n bigdata-devops
kubectl rollout undo deployment/frontend -n bigdata-devops

# Option 2: Rebuild previous build in Jenkins
# Go to Jenkins → Your Pipeline → Build #<previous> → Rebuild

# Option 3: Manual image update
kubectl set image deployment/backend -n bigdata-devops \
  backend=siddharth194/bigdata-devops:backend-<PREVIOUS_BUILD>
```

## Security Considerations

1. **Use Jenkins Credentials** - Never hardcode passwords
2. **Secure Jenkins** - Enable authentication and authorization
3. **GitHub Webhook Secret** - Add secret for webhook validation
4. **Docker Hub Access Token** - Use tokens instead of passwords
5. **Kubernetes RBAC** - Configure proper access controls
6. **Network Policies** - Restrict pod-to-pod communication

## Performance Optimization

1. **Docker Layer Caching** - Optimize Dockerfiles
2. **Parallel Stages** - Run independent stages in parallel
3. **Resource Limits** - Set appropriate CPU/memory limits
4. **Build Artifacts** - Clean up old artifacts regularly

## Viewing Deployment Results

After successful pipeline run:

```bash
# Check all resources
kubectl get all -n bigdata-devops

# Access applications
minikube service list -n bigdata-devops

# View logs
kubectl logs -n bigdata-devops -l app=backend --tail=50
kubectl logs -n bigdata-devops -l app=frontend --tail=50

# Check autoscaling
kubectl top pods -n bigdata-devops
kubectl get hpa -n bigdata-devops
```

## Next Steps

1. ✅ Set up Jenkins
2. ✅ Configure credentials
3. ✅ Create pipeline job
4. ✅ Configure GitHub webhook
5. ✅ Test with manual trigger
6. ✅ Test with Git push
7. ✅ Monitor and verify deployment
8. ✅ Set up alerts/notifications (optional)

## Additional Resources

- Jenkins Documentation: https://www.jenkins.io/doc/
- Ansible Documentation: https://docs.ansible.com/
- Kubernetes Documentation: https://kubernetes.io/docs/
- Minikube Documentation: https://minikube.sigs.k8s.io/docs/
