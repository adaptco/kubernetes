FROM python:3.11-slim

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Copy shared libs
COPY ../../lib /app/lib
COPY ../../schemas /app/schemas

CMD ["celery", "-A", "worker", "worker", "-l", "info", "-Q", "embed_queue"]
