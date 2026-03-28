FROM python:3.12-slim

# Install system utilities needed and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies into uv managed environment
ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync --frozen --no-dev

# Copy the application code
COPY . .

# Expose port
EXPOSE 8000

# Start django development server by default
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
