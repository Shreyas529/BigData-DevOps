#!/bin/bash

# Deployment verification script

set -e

NAMESPACE="bigdata-devops"

echo "================================================"
echo "  Deployment Verification"
echo "================================================"
echo ""

# Check if namespace exists
echo "📋 Checking namespace..."
if kubectl get namespace $NAMESPACE &> /dev/null; then
    echo "✅ Namespace '$NAMESPACE' exists"
else
    echo "❌ Namespace '$NAMESPACE' not found"
    exit 1
fi

echo ""
echo "📦 Checking deployments..."
kubectl get deployments -n $NAMESPACE

echo ""
echo "🔄 Checking pods..."
kubectl get pods -n $NAMESPACE

echo ""
echo "🌐 Checking services..."
kubectl get services -n $NAMESPACE

echo ""
echo "📊 Checking HPA..."
kubectl get hpa -n $NAMESPACE

echo ""
echo "💾 Checking PVCs..."
kubectl get pvc -n $NAMESPACE

echo ""
echo "🔧 Checking ConfigMaps..."
kubectl get configmaps -n $NAMESPACE

echo ""
echo "🔐 Checking Secrets..."
kubectl get secrets -n $NAMESPACE

echo ""
echo "================================================"
echo "  Service URLs"
echo "================================================"

echo ""
echo "Frontend:"
minikube service frontend -n $NAMESPACE --url || echo "❌ Frontend service not ready"

echo ""
echo "Kibana:"
minikube service kibana -n $NAMESPACE --url || echo "❌ Kibana service not ready"

echo ""
echo "================================================"
echo "  Resource Usage"
echo "================================================"

echo ""
kubectl top nodes 2>/dev/null || echo "⚠️  Metrics not available (metrics-server may still be starting)"

echo ""
kubectl top pods -n $NAMESPACE 2>/dev/null || echo "⚠️  Pod metrics not available yet"

echo ""
echo "================================================"
echo "  Recent Events"
echo "================================================"

kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -10

echo ""
echo "================================================"
echo "  Verification Complete"
echo "================================================"
