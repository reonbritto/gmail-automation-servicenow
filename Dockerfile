# Use multi-stage build for smaller final image
FROM python:3.11-slim AS builder

# Set build environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /build

# Install only necessary build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        fastapi \
        uvicorn \
        crewai \
        crewai-tools \
        beautifulsoup4 \
        pydantic \
        requests \
        python-dotenv \
        imaplib2

# Copy source code and project files before running crewai install
COPY ./src ./src
COPY pyproject.toml uv.lock ./

# Optionally install crewai dependencies if pyproject.toml exists
RUN if [ -f pyproject.toml ]; then crewai install || true; fi

# Start second stage with clean image
FROM python:3.11-slim

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set environment variables
ENV PYTHONPATH=/app/src

# Set work directory
WORKDIR /app

# Copy application source code
COPY ./src ./src

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "gmail_crew_ai.api:app", "--host", "0.0.0.0", "--port", "8000"]
