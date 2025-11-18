# Claude Plays Zelda - Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    # Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-eng \
    # Build tools
    gcc \
    g++ \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 zelda

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=zelda:zelda . .

# Install the package
RUN pip install --no-cache-dir -e .

# Create data directories
RUN mkdir -p data/screenshots data/saves data/logs data/highlights \
    && chown -R zelda:zelda data

# Switch to non-root user
USER zelda

# Expose ports
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Default command
CMD ["python", "-m", "claude_plays_zelda.cli", "play"]
