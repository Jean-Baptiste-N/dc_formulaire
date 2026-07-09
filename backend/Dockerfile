# DC Formulaire
# Container with the backend of the application, using Python 3.12 and Gunicorn as the WSGI server.
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code to the container
COPY app/ .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create staticfiles directory with proper permissions
RUN mkdir -p /app/staticfiles && chmod -R 755 /app/staticfiles

#  Expose port 8001 for the application
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/ || exit 1

# Installer Trivy pour scanner
RUN apt-get update && apt-get install -y curl && \
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Use entrypoint to run the application
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8001", "--workers", "4", "--timeout", "600", "--access-logfile", "-", "--error-logfile", "-"]
