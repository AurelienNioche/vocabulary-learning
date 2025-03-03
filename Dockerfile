FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY pyproject.toml .
COPY README.md .

# Install dependencies
RUN pip install --no-cache-dir build && \
    python -m build --wheel --no-isolation

FROM python:3.10-slim

# Add metadata labels
LABEL maintainer="Aurelien Nioche" \
      description="Japanese Vocabulary Learning Tool" \
      version="1.0.0"

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m -s /bin/bash appuser && \
    mkdir -p /app/vocabulary_learning/data /app/firebase && \
    chown -R appuser:appuser /app

# Copy wheel from builder
COPY --from=builder /app/dist/*.whl /app/

# Install the package
RUN pip install --no-cache-dir /app/*.whl && \
    rm /app/*.whl

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Switch to non-root user
USER appuser

# Set the entrypoint
ENTRYPOINT ["vocab"] 