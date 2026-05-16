FROM python:3.11-slim

WORKDIR /app

# Install build deps for some packages if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . /app

# Add DB wait script and make it executable
RUN chmod +x /app/wait-for-db.sh || true

ENV PYTHONUNBUFFERED=1
EXPOSE 5000

CMD ["python", "app.py"]
