# Claude Plays Zelda - Production Dockerfile

# Build stage for Python dependencies
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --target=/install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install runtime dependencies only
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
    # NES Emulator
    fceux \
    # X11 / Headless support
    xvfb \
    x11-utils \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local/lib/python3.11/site-packages

# Create app user
RUN useradd -m -u 1000 zelda

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=zelda:zelda . .

# Install the package (production install, not editable)
RUN pip install --no-cache-dir --no-deps .

# Create data directories
RUN mkdir -p data/screenshots data/saves data/logs data/highlights \
    && chown -R zelda:zelda data

# Switch to non-root user
USER zelda

# Expose ports
EXPOSE 5000

# Health check (only applicable if web server is running)
# Note: The default command runs the game agent, not the web server
# To use health check, override CMD to run the web server
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Default command
# Default command with Xvfb for headless execution
CMD ["xvfb-run", "--auto-servernum", "--server-args='-screen 0 1024x768x24'", "python", "main.py"]
