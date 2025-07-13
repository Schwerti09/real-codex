FROM python:3.11-slim

# System libs required for gymnasium and pqcrypto
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libgl1 libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "-m", "bioreactor_network_optimization"]
