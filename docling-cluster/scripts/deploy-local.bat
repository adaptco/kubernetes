@echo off
REM Build and deploy script for local development (Windows)

echo === Docling Cluster - Local Deployment ===

echo Building images...
docker-compose build

echo Starting services...
docker-compose up -d

echo Waiting for services to be healthy...
timeout /t 5 /nobreak > nul

echo Checking service health...
curl -s http://localhost:8000/health

echo.
echo === Deployment Complete ===
echo Ingest API: http://localhost:8000
echo Qdrant:     http://localhost:6333
echo.
echo To ingest a document:
echo   curl -X POST http://localhost:8000/ingest -F "file=@document.pdf"
echo.
echo To view logs:
echo   docker-compose logs -f

pause
