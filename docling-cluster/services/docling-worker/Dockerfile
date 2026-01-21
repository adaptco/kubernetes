FROM python:3.11-slim

WORKDIR /app

# Install system deps for Docling
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Copy shared libs
COPY ../../lib /app/lib
COPY ../../schemas /app/schemas

CMD ["celery", "-A", "worker", "worker", "-l", "info", "-Q", "parse_queue"]
