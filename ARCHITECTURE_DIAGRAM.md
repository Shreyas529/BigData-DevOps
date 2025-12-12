# Complete CI/CD Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DEVELOPER WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────┘

    Developer                GitHub Repository              Jenkins Server
        │                           │                              │
        │  1. git push              │                              │
        ├──────────────────────────>│                              │
        │                           │                              │
        │                           │   2. Web Hook                │
        │                           ├─────────────────────────────>│
        │                           │                              │
        │                           │                              │  3. Pull Code
        │                           │<─────────────────────────────┤
        │                           │                              │


┌─────────────────────────────────────────────────────────────────────┐
│                      JENKINS CI/CD PIPELINE                         │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ 1. Cleanup       │  Remove old Docker images and containers
│    Previous      │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ 2. Checkout      │  Pull latest code from GitHub main branch
│    Code          │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ 3. Run Tests     │  docker-compose.test.yml
│                  │  - Start test database
│                  │  - Run pytest tests
│                  │  - Fail pipeline if tests fail
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ 4. Build Images  │  Build Docker images:
│                  │  - backend:backend-<BUILD_NUMBER>
│                  │  - frontend:frontend-<BUILD_NUMBER>
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ 5. Push to       │  Push images to Docker Hub
│    DockerHub     │  - siddharth194/bigdata-devops:backend-123
│                  │  - siddharth194/bigdata-devops:frontend-123
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ 6. Pull Images   │  Verify images are available
│    (Verify)      │
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ 7. Update K8s    │  Update image tags in:
│    Manifests     │  - backend-deployment.yaml
│                  │  - frontend-deployment.yaml
│                  │  - consumer-deployment.yaml
│                  │  - db-init-job.yaml
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ 8. Deploy via    │  Run: ansible-playbook playbook-with-roles.yaml
│    Ansible       │  - Install Ansible dependencies
│                  │  - Verify Minikube running
│                  │  - Deploy to bigdata-devops namespace
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ 9. Verify        │  - Wait for pods ready
│    Deployment    │  - Check services
│                  │  - Display URLs
└──────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                   KUBERNETES/MINIKUBE DEPLOYMENT                    │
└─────────────────────────────────────────────────────────────────────┘

Namespace: bigdata-devops

┌─────────────────────────────────────────────────────────────┐
│  Infrastructure Layer                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐           ┌──────────────┐            │
│  │  Kafka (KRaft)   │           │ PostgreSQL   │            │
│  │    (1 pod)       │           │   (1 pod)    │            │
│  └──────────────────┘           └──────┬───────┘            │
│                                        │                    │
│                                        v                    │
│                                 ┌──────────────┐            │
│                                 │  DB Init Job │            │
│                                 │ (Runs once)  │            │
│                                 └──────────────┘            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Logging Stack (ELK)                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐   ┌──────────┐    ┌──────────┐            │
│  │Elasticsearch │<──│ Logstash │<───│  Kibana  │            │
│  │   (1 pod)    │   │ (1 pod)  │    │ (1 pod)  │            │
│  └──────────────┘   └──────────┘    └────┬─────┘            │
│                                          │                  │
│                                          └─> NodePort       │
│                                              :5601          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Application Layer                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐             │
│  │ Backend  │────>│ Consumer │     │ Frontend │             │
│  │ (2+ pods)│     │(2+ pods) │     │(2+ pods) │             │
│  │   :5002  │     │          │     │  :8501   │             │
│  └────┬─────┘     └──────────┘     └────┬─────┘             │
│       │                                  │                  │
│       │ ClusterIP                        └─> NodePort       │
│       │                                      (External)     │
│       └───────────────────────────────────────────────>     │
│                   Logs to Logstash                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Autoscaling (HPA)                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Backend:  2 - 10 pods  (CPU: 70%, Memory: 80%)             │
│  Frontend: 2 - 8 pods   (CPU: 70%, Memory: 80%)             │
│  Consumer: 2 - 6 pods   (CPU: 75%, Memory: 85%)             │
│                                                             │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                   │
└─────────────────────────────────────────────────────────────────────┘

User ──> Frontend ──> Backend ──> Kafka ──> Consumer ──> PostgreSQL
  ^        (8501)      (5002)      (9092)     (*)         (5432)
  │                                 │          │
  │                                 └──────────┴────> Logstash ──> Elasticsearch ──> Kibana
  │                                                     (5044)         (9200)        (5601)
  │                                                                                     │
  └─────────────────────────────────────────────────────────────────────────────────>│
                                View Logs & Metrics


┌─────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT CHARACTERISTICS                       │
└─────────────────────────────────────────────────────────────────────┘

✅ Init Containers:
   - Kafka runs in KRaft mode (no Zookeeper dependency)
   - Backend waits for Kafka + Logstash
   - Consumer waits for Kafka + PostgreSQL + Logstash
   - Frontend waits for Backend
   - ELK components wait for Elasticsearch

✅ ConfigMaps:
   - Application environment variables
   - Logstash pipeline configuration
   - ELK Java memory settings

✅ Secrets:
   - PostgreSQL credentials
   - Kafka connection strings
   - Docker Hub credentials

✅ Health Checks:
   - Liveness Probes: Auto-restart unhealthy containers
   - Readiness Probes: Control traffic routing
   - Implemented on all critical services

✅ Persistent Storage:
   - PostgreSQL: 5Gi PVC
   - Elasticsearch: 10Gi PVC

✅ Rolling Updates:
   - Zero-downtime deployments
   - Gradual pod replacement
   - Health checks ensure smooth transitions


┌─────────────────────────────────────────────────────────────────────┐
│                      ACCESS POINTS                                  │
└─────────────────────────────────────────────────────────────────────┘

Frontend Application:
  minikube service frontend -n bigdata-devops --url
  http://<MINIKUBE_IP>:<NODE_PORT>

Kibana Dashboard:
  minikube service kibana -n bigdata-devops --url
  http://<MINIKUBE_IP>:<NODE_PORT>

Backend API (Internal):
  http://backend.bigdata-devops.svc.cluster.local:5002

PostgreSQL (Internal):
  postgres.bigdata-devops.svc.cluster.local:5432


┌─────────────────────────────────────────────────────────────────────┐
│                      MONITORING & DEBUGGING                         │
└─────────────────────────────────────────────────────────────────────┘

Check Pods:
  kubectl get pods -n bigdata-devops

View Logs:
  kubectl logs -n bigdata-devops -l app=backend --tail=50
  kubectl logs -n bigdata-devops -l app=frontend --tail=50

Check Autoscaling:
  kubectl get hpa -n bigdata-devops
  kubectl top pods -n bigdata-devops

Service Status:
  kubectl get svc -n bigdata-devops
  minikube service list -n bigdata-devops

Events:
  kubectl get events -n bigdata-devops --sort-by='.lastTimestamp'


┌─────────────────────────────────────────────────────────────────────┐
│                    ROLLBACK PROCEDURE                               │
└─────────────────────────────────────────────────────────────────────┘

1. Via Jenkins:
   - Go to previous successful build
   - Click "Rebuild"

2. Via kubectl:
   kubectl rollout undo deployment/backend -n bigdata-devops
   kubectl rollout undo deployment/frontend -n bigdata-devops

3. Manual image update:
   kubectl set image deployment/backend -n bigdata-devops \
     backend=siddharth194/bigdata-devops:backend-<PREVIOUS_BUILD>
```
