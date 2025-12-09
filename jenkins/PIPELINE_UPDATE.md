# Jenkins Pipeline Update Summary

## ✅ Changes Made to Jenkinsfile

### 1. **Added Git Trigger Configuration**
```groovy
triggers {
    pollSCM('H/5 * * * *')  // Polls every 5 minutes
    // githubPush()          // Or use webhook for instant trigger
}
```

### 2. **New Stage: Update Kubernetes Manifests**
- Automatically updates image tags in K8s deployment files
- Uses `sed` to replace image tags with current BUILD_NUMBER
- Updates: backend, frontend, consumer, and db-init-job

### 3. **New Stage: Deploy to Minikube via Ansible**
- Checks and installs Ansible if needed
- Installs Kubernetes Ansible collection
- Verifies Minikube is running (starts if needed)
- Runs Ansible playbook with build-specific image tags
- Passes Docker credentials securely

### 4. **New Stage: Verify Deployment**
- Waits for pods to be ready
- Displays deployment status (pods, services, HPA)
- Shows service URLs for frontend and Kibana

### 5. **Enhanced Post Actions**
- Better success/failure messages
- Displays build information
- Shows service URLs after deployment

## 📊 Complete Pipeline Flow

```
1. Git Push/Webhook Trigger
   ↓
2. Cleanup Previous Build
   ↓
3. Checkout Code from GitHub
   ↓
4. Run Tests (docker-compose.test.yml)
   ↓
5. Build Docker Images
   - backend:backend-<BUILD_NUMBER>
   - frontend:frontend-<BUILD_NUMBER>
   ↓
6. Push to DockerHub
   ↓
7. Pull Images (Verification)
   ↓
8. Update K8s Manifests
   - Updates image tags in YAML files
   ↓
9. Deploy via Ansible
   - Installs dependencies
   - Runs playbook-with-roles.yaml
   - Deploys to bigdata-devops namespace
   ↓
10. Verify Deployment
    - Check pod status
    - Display service URLs
   ↓
11. Success/Failure Notification
```

## 🎯 Key Features

### Automated CI/CD Pipeline
- ✅ **Continuous Integration**: Tests run automatically on every push
- ✅ **Continuous Deployment**: Successful builds deploy automatically
- ✅ **Image Versioning**: Each build gets unique BUILD_NUMBER tag
- ✅ **Rollback Support**: Previous images remain in DockerHub

### Deployment Automation
- ✅ **Ansible Integration**: Uses role-based playbook for deployment
- ✅ **Dependency Management**: Auto-installs Ansible and K8s tools
- ✅ **Health Checks**: Waits for pods to be ready
- ✅ **Service Discovery**: Automatically gets service URLs

### Security
- ✅ **Credential Binding**: Docker Hub credentials injected securely
- ✅ **No Hardcoded Secrets**: All credentials from Jenkins vault
- ✅ **GitHub Integration**: Secure token-based authentication

## 🚀 How to Use

### Initial Setup

1. **Configure Jenkins Credentials**:
   - `dockerhub-credentials`: Docker Hub username/password
   - `github-credentials`: GitHub username/token

2. **Install Required Tools on Jenkins Server**:
   ```bash
   # Docker, Minikube, kubectl, Ansible
   # See jenkins/JENKINS_SETUP.md for details
   ```

3. **Start Minikube**:
   ```bash
   minikube start --memory=8192 --cpus=4
   ```

4. **Create Jenkins Pipeline Job**:
   - New Item → Pipeline
   - Configure SCM: https://github.com/Shreyas529/BigData-DevOps.git
   - Script Path: jenkins/Jenkinsfile

### Trigger Deployment

#### Option 1: Automatic (Recommended)
```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Jenkins automatically detects and builds
# Within 5 minutes (or instant with webhook)
```

#### Option 2: Manual
- Go to Jenkins → Your Pipeline
- Click "Build Now"

### Monitor Deployment

```bash
# Watch Jenkins console output
# Or check deployment status:

kubectl get pods -n bigdata-devops
kubectl get svc -n bigdata-devops
minikube service frontend -n bigdata-devops --url
```

## 📝 Environment Variables

The pipeline uses these variables:

| Variable | Value | Purpose |
|----------|-------|---------|
| `DOCKER_HUB_CREDENTIALS` | `dockerhub-credentials` | Jenkins credential ID |
| `IMAGE_NAME` | `siddharth194/bigdata-devops` | Docker repository |
| `BACKEND_TAG` | `backend` | Backend image tag prefix |
| `FRONTEND_TAG` | `frontend` | Frontend image tag prefix |
| `BUILD_NUMBER` | Auto-generated | Jenkins build number |

## 🔄 Deployment Process Details

### Stage: Update Kubernetes Manifests
```bash
# Updates image references in K8s YAML files
sed -i 's|image: repo:backend-.*|image: repo:backend-123|g' k8s/*.yaml
```

### Stage: Deploy to Minikube via Ansible
```bash
# Runs Ansible with build-specific variables
ansible-playbook playbook-with-roles.yaml \
  -e "docker_username=$DOCKER_USER" \
  -e "docker_password=$DOCKER_PASS" \
  -e "build_number=123"
```

### Stage: Verify Deployment
```bash
# Waits for pods and displays status
kubectl wait --for=condition=ready pod -l app=backend -n bigdata-devops
kubectl get pods -n bigdata-devops
```

## 🐛 Troubleshooting

### Pipeline fails at "Deploy to Minikube"
**Solution**: Ensure Minikube is running
```bash
minikube status
minikube start --memory=8192 --cpus=4
```

### Pipeline fails at "Run Tests"
**Solution**: Check test logs in Jenkins console
```bash
docker compose -f docker-compose.test.yml logs
```

### Images not pushing to DockerHub
**Solution**: Verify Docker Hub credentials
- Check credentials in Jenkins
- Test: `docker login -u <username>`

### Deployment successful but services not accessible
**Solution**: Check Minikube service status
```bash
kubectl get svc -n bigdata-devops
minikube service list -n bigdata-devops
```

## 📚 Documentation Files

- **`jenkins/Jenkinsfile`** - Complete pipeline definition
- **`jenkins/JENKINS_SETUP.md`** - Detailed Jenkins setup guide
- **`ansible/README.md`** - Ansible deployment guide
- **`k8s/README.md`** - Kubernetes manifests guide
- **`DEPLOYMENT_SUMMARY.md`** - Overall implementation summary
- **`QUICK_REFERENCE.md`** - Command reference card

## ✅ Requirements Met

All CI/CD requirements are now implemented:

- ✅ Jenkins fetches and builds updated code
- ✅ Automated tests run on every build
- ✅ Docker images pushed to Docker Hub
- ✅ Images deployed to Minikube via Ansible
- ✅ Changes visible after application refresh
- ✅ Logs feed into ELK Stack
- ✅ Git push triggers automated pipeline

## 🎉 Result

Your complete CI/CD pipeline is now active:

1. **Push code** → GitHub
2. **Jenkins detects** → Automatically triggers
3. **Tests run** → Ensures quality
4. **Images build** → Tagged with BUILD_NUMBER
5. **Push to DockerHub** → Versioned artifacts
6. **Ansible deploys** → To Minikube
7. **Services live** → Accessible via Minikube URLs
8. **Logs visible** → In Kibana dashboard

The entire process from code push to live deployment is fully automated! 🚀
