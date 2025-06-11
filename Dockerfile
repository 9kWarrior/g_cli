FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /tmp/* /root/.cache/pip

COPY github_cli/ ./github_cli/

ENTRYPOINT ["python", "github_cli/cli.py"]