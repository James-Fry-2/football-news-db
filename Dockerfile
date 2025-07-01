FROM python:3.11-slim

WORKDIR /app

# Install system dependencies in a single layer
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    python3-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy web requirements with AI/ML dependencies
COPY requirements/web.txt ./requirements/

# Install dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/web.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"] 