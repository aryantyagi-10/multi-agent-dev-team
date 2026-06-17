# Multi-Agent Software Development Team

Microservices multi-agent system: a Product Manager, Developer, and QA Engineer
agent collaborate (with a fix-loop) to turn a feature request into tested code.

## Stack
Streamlit · FastAPI · JWT · Kafka · Redis · PostgreSQL · LangGraph · MCP tools

## Run locally (Windows + WSL2 + Docker Desktop)

1. Clone INSIDE the WSL2 filesystem (e.g. `\\wsl$\Ubuntu\home\you\`) for fast I/O.
2. Copy env: `cp .env.example .env` and set `OPENAI_API_KEY` + `JWT_SECRET_KEY`.
3. Build & start:
