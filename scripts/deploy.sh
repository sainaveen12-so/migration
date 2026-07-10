#!/bin/bash
set -e

echo "=== AI Code Migration Tool - Deployment Script ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "Docker Compose is required."; exit 1; }

COMPOSE_CMD="docker compose"
if ! docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
fi

# Create .env if not exists
if [ ! -f .env ]; then
  echo "Creating .env from template..."
  cp backend/.env.example .env
  echo "Please edit .env with your API keys and secrets before production use."
fi

echo "Building and starting services..."
$COMPOSE_CMD up -d --build

echo "Waiting for services to be healthy..."
sleep 10

echo "Running database migrations..."
$COMPOSE_CMD exec -T backend alembic upgrade head

echo ""
echo "=== Deployment Complete ==="
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo "Metrics:   http://localhost:8000/metrics"
echo ""
echo "To enable local AI (Ollama):"
echo "  $COMPOSE_CMD --profile local-ai up -d ollama"
echo "  docker exec -it migration-ollama-1 ollama pull llama3.2"
