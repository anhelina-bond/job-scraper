FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install system dependencies for psycopg2 and pdf processing
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-cache --no-install-project

# Copy the rest of the code
COPY . .

# Create directory for uploads and vector db
RUN mkdir -p uploads chroma_db

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI using uv
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]