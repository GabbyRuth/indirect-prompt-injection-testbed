FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt-get/lists/*
    
WORKDIR /app

RUN mkdir -p /app/assets

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN useradd -m sandbox && chown -R sandbox:sandbox /app
USER sandbox

CMD ["python", "Docker/runner.py"]