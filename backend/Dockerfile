# ===== Frontend Builder Stage =====
FROM node:18-alpine as frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package.json ./

# Install frontend dependencies
RUN npm install && npm cache clean --force

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# ===== Backend Stage =====
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Copy frontend build artifacts from frontend-builder stage
COPY --from=frontend-builder /frontend/dist/spa ./static

# Create directory for database
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
