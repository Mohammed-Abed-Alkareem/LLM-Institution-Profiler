# --- Stage 1: Build dependencies ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools temporarily
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# --- Stage 2: Runtime environment ---
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy Python dependencies only
COPY --from=builder /install /usr/local

# Copy app source code
COPY . .

# Use non-root user for security
RUN adduser --disabled-password flaskuser && \
    chown -R flaskuser /app
USER flaskuser

# Expose port
EXPOSE 5000

# Start the app using gunicorn
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "wsgi:app"]
