# syntax=docker/dockerfile:1.7

# Use a slim Python base image
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and force stdout/stderr to be unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set workdir
WORKDIR /app

# System dependencies (minimal). psycopg2-binary ships its own libpq.
# Add build tools only if a package needs compilation; wheels cover common platforms.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port Gunicorn will bind to
EXPOSE 5000

# Set default environment (override in runtime/compose)
ENV FLASK_ENV=production \
    PORT=5000

# Use Gunicorn to serve the Flask app defined in main.py as `app`
# -c gunicorn.conf.py allows overrides without changing the Dockerfile
CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:app"]
