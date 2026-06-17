FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc librdkafka-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the package into /app/backend so `python -m backend.entrypoint` works
COPY . /app/backend
WORKDIR /app

EXPOSE 8000
CMD ["python", "-m", "backend.entrypoint"]
