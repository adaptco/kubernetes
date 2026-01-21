# Docling Normalization Cluster

A deterministic document processing pipeline:
**Docling → Canonical JSON → Embeddings → Vector Store**

## Quick Start

```bash
# Start all services
docker-compose up --build

# Ingest a document
curl -X POST http://localhost:8000/ingest \
  -F "file=@document.pdf"
```

## Services

| Service | Port | Description |
| --------- | ------ | ------------- |
| ingest-api | 8000 | Document ingestion API |
| qdrant | 6333 | Vector store |
| redis | 6379 | Message queue |

## Architecture

```text
PDF → ingest-api → parse_queue → docling-worker → embed_queue → embed-worker → Qdrant
                                       ↓                              ↓
                                   ledger                          ledger
```
