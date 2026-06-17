import json
import redis
from confluent_kafka import Consumer

from backend.config import settings
from backend.database import SyncSessionLocal
from backend.models import Job
from backend.agents.graph import compiled_graph

_redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def _update_job(job_id: str, **fields):
    with SyncSessionLocal() as db:
        job = db.get(Job, job_id)
        if job:
            for k, v in fields.items():
                setattr(job, k, v)
            db.commit()


def process_job(job_id: str, prompt: str):
    _update_job(job_id, status="running")
    _redis.set(f"job:{job_id}:status", "running", ex=3600)
    try:
        final = compiled_graph.invoke(
            {"job_id": job_id, "prompt": prompt, "iterations": 0, "logs": []},
            config={"recursion_limit": 25},
        )
        _update_job(
            job_id,
            status="done",
            result_code=final.get("code", ""),
            result_tests=final.get("test_code", ""),
        )
        _redis.set(f"job:{job_id}:status", "done", ex=3600)
    except Exception as e:  # noqa: BLE001
        _update_job(job_id, status="failed", result_code=f"ERROR: {e}")
        _redis.set(f"job:{job_id}:status", "failed", ex=3600)
        _redis.rpush(
            f"job:{job_id}:logs",
            json.dumps({"agent": "System", "message": f"Worker error: {e}"}),
        )


def run_worker():
    consumer = Consumer({
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "group.id": "agent_workers",
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe([settings.KAFKA_JOB_TOPIC])
    print("[worker] Consuming from Kafka topic:", settings.KAFKA_JOB_TOPIC, flush=True)
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("[worker] Kafka error:", msg.error(), flush=True)
                continue
            data = json.loads(msg.value().decode("utf-8"))
            print("[worker] Got job:", data["job_id"], flush=True)
            process_job(data["job_id"], data["prompt"])
            consumer.commit(msg)
    finally:
        consumer.close()


if __name__ == "__main__":
    run_worker()
