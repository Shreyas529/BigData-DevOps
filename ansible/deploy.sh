#!/bin/bash

# Quick deployment script for BigData-DevOps to Minikube

set -e

echo "================================================"
echo "  BigData-DevOps Minikube Deployment Script"
echo "================================================"
echo ""

# Check if Minikube is installed
if ! command -v minikube &> /dev/null; then
    echo "❌ Error: minikube is not installed"
    echo "Please install minikube: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ Error: kubectl is not installed"
    echo "Please install kubectl: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if Ansible is installed
if ! command -v ansible-playbook &> /dev/null; then
    echo "❌ Error: ansible is not installed"
    echo "Installing Ansible..."
    pip install ansible
fi

# Check Minikube status
echo "📋 Checking Minikube status..."
if ! minikube status &> /dev/null; then
    echo "🚀 Starting Minikube..."
    minikube start --memory=8192 --cpus=4 --driver=docker
else
    echo "✅ Minikube is already running"
fi

# Enable metrics-server for HPA
echo "📊 Enabling metrics-server..."
minikube addons enable metrics-server

# Install Kubernetes Ansible collection if not present
echo "📦 Installing Ansible Kubernetes collection..."
ansible-galaxy collection install kubernetes.core --force

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -q kubernetes openshift

# Set kubectl context
echo "🔧 Setting kubectl context to minikube..."
kubectl config use-context minikube

# Run Ansible playbook
echo ""
echo "🚀 Starting deployment with Ansible..."
echo ""

cd "$(dirname "$0")"

if [ -f "playbook-with-roles.yaml" ]; then
    ansible-playbook -i inventory.ini playbook-with-roles.yaml
else
    ansible-playbook -i inventory.ini playbook.yaml
fi

echo ""
echo "================================================"
echo "  Deployment Complete!"
echo "================================================"
echo ""
echo "📊 Check deployment status:"
echo "   kubectl get pods -n bigdata-devops"
echo ""
echo "🌐 Access services:"
echo "   Frontend: minikube service frontend -n bigdata-devops"
echo "   Kibana:   minikube service kibana -n bigdata-devops"
echo ""
echo "📈 Monitor autoscaling:"
echo "   kubectl get hpa -n bigdata-devops"
echo "   kubectl top pods -n bigdata-devops"
echo ""
echo "================================================"
