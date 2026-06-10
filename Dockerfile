# Multi-stage build for FallGuard - Cloud Run optimized
# Stage 1: Builder
FROM python:3.11 as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install to /install directory
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
# Use full Python image (not slim) for better system library support
FROM python:3.11

WORKDIR /app

# Install runtime dependencies for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY main.py .
COPY fallguard/ ./fallguard/

# Ensure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

# Cloud Run requires listening on PORT env var (defaults to 8080)
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
