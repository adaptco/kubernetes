#!/bin/bash
# Build and deploy script for local development

set -e

echo "=== Docling Cluster - Local Deployment ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker required but not installed. Aborting."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "docker-compose required but not installed. Aborting."; exit 1; }

echo "Building images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Waiting for services to be healthy..."
sleep 5

echo "Checking service health..."
curl -s http://localhost:8000/health | python -m json.tool

echo ""
echo "=== Deployment Complete ==="
echo "Ingest API: http://localhost:8000"
echo "Qdrant:     http://localhost:6333"
echo ""
echo "To ingest a document:"
echo "  curl -X POST http://localhost:8000/ingest -F 'file=@document.pdf'"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
