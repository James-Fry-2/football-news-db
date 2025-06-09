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

# Copy minimal web requirements for faster build
COPY requirements/web_minimal.txt ./requirements/

# Install dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/web_minimal.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"] 