import uuid
import json
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db, init_models
from backend.models import User, Job
from backend.schemas import UserCreate, Token, JobCreate, JobOut
from backend.auth import (
    hash_password, verify_password, create_access_token, decode_token
)
from backend.kafka_producer import publish_job

aredis = aioredis.from_url(settings.redis_url, decode_responses=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    yield


app = FastAPI(title="Multi-Agent Dev Team API", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=Token)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.scalar(select(User).where(User.username == payload.username))
    if exists:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already taken")
    user = User(username=payload.username, hashed_password=hash_password(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return Token(access_token=create_access_token(user.username, user.id))


@app.post("/auth/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(select(User).where(User.username == form.username))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bad credentials")
    return Token(access_token=create_access_token(user.username, user.id))


@app.post("/jobs", response_model=JobOut)
async def create_job(
    payload: JobCreate,
    user=Depends(decode_token),
    db: AsyncSession = Depends(get_db),
):
    job_id = str(uuid.uuid4())
    job = Job(id=job_id, owner_id=user["uid"], prompt=payload.prompt, status="queued")
    db.add(job)
    await db.commit()
    # Decouple: hand off to Kafka, return immediately
    publish_job(job_id, payload.prompt, user["uid"])
    return JobOut(id=job_id, status="queued", prompt=payload.prompt)


@app.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(
    job_id: str,
    user=Depends(decode_token),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(Job, job_id)
    if not job or job.owner_id != user["uid"]:  # tenant isolation
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return job


@app.get("/jobs/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    after: int = 0,
    user=Depends(decode_token),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(Job, job_id)
    if not job or job.owner_id != user["uid"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    raw = await aredis.lrange(f"job:{job_id}:logs", after, -1)
    logs = [json.loads(x) for x in raw]
    status_val = await aredis.get(f"job:{job_id}:status") or job.status
    return {"logs": logs, "status": status_val, "next_index": after + len(logs)}
