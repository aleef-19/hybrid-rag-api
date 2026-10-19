# Hybrid RAG API

A local Hybrid RAG (Retrieval-Augmented Generation) API built with FastAPI, PostgreSQL (`pgvector`), Redis caching, and Docker.

## Getting Started Locally

### 1. Clone the repository
```bash
git clone [https://github.com/aleef-19/hybrid-rag-api.git](https://github.com/aleef-19/hybrid-rag-api.git)
cd hybrid-rag-api

cp .env.example .env

docker compose up -d

pip install -r requirements.txt

uvicorn app.main:app --reload
