# Production Dockerfile for ASD Orchestrator
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE_DIR=/app/workspace

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install project dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install bandit  # Hard security gate dependency

# Copy application code
COPY src/ ./src/
COPY .asd/ ./.asd/
COPY config/ ./config/
COPY README.md AGENTS.md architecture.md ./

# Create workspace and logs directory
RUN mkdir -p /app/workspace /app/logs /app/research

# Set Python path to include src and .asd
ENV PYTHONPATH="/app/src:/app/.asd:${PYTHONPATH}"

# Default command (Can be overridden to run specific phases)
ENTRYPOINT ["python", "src/orchestrator.py"]
CMD ["--help"]
