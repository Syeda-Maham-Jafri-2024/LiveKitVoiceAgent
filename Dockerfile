
# Use official Python image
ARG PYTHON_VERSION=3.13.1
FROM python:${PYTHON_VERSION} AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Load environment variables from .env (if needed)
ENV ENV_PATH=/app/.env

# Run the application
CMD ["python", "main.py"]
