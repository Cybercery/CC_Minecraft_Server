FROM python:3.11-slim

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser && \
    mkdir /data && chown appuser:appgroup /data && \
    apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# create empty monitoring/ and storage/ directories so COPY doesn't fail
RUN mkdir monitoring storage

COPY backend/ ./backend/
# Use optional copy in case they don't exist yet, wait COPY doesn't support optional, so we'll create empty dirs before docker build
COPY monitoring/ ./monitoring/
COPY storage/ ./storage/

USER 10001
ENV PYTHONPATH=/app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
