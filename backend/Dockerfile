FROM python:3.11-slim

WORKDIR /app

# Install system deps needed by psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 3001

CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "3001"]
