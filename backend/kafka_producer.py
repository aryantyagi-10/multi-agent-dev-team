import json
from confluent_kafka import Producer

from backend.config import settings

_producer: Producer | None = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})
    return _producer


def publish_job(job_id: str, prompt: str, user_id: int):
    p = get_producer()
    payload = json.dumps({"job_id": job_id, "prompt": prompt, "user_id": user_id})
    p.produce(settings.KAFKA_JOB_TOPIC, value=payload.encode("utf-8"))
    p.flush(5)
