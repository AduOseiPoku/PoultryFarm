FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATA_DIR=/app/data

WORKDIR /app

# Install system dependencies (libpq-dev for PostgreSQL, curl for Docker health check)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project codebase
COPY . /app/

# Create directories for persistent volume storage and static files
RUN mkdir -p /app/data /app/staticfiles

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh

# Collect static files during build
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Docker health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
