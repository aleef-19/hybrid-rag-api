from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import init_db, get_db, DocumentChunk
from app.chunker import extract_text, chunk_text
from app.embeddings import generate_embedding, generate_embeddings
from app.cache import get_cached_result, set_cached_result, clear_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title= "Hybrid RAG API", lifespan = lifespan)

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_bytes = await file.read()

    try:
        text = extract_text(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Document is empty.")

    embeddings = generate_embeddings(chunks)

    for idx, (chunk_str, emb) in enumerate(zip(chunks,embeddings)): 
        db_chunk = DocumentChunk(
            filename = file.filename,
            chunk_index = idx,
            content = chunk_str,
            embedding = emb
        )
        db.add(db_chunk)

    db.commit()
    clear_cache()

    return {
        "filename": file.filename,
        "chunks_stored": len(chunks),
        "message": "Document processed and stored successfully."
    }

@app.post("/search")
def hybrid_search(request: SearchRequest, db: Session = Depends(get_db)):
    cached = get_cached_result(request.query, request.top_k)
    if cached is not None:
        return {"source": "redis_cache", "results": cached}
    query_embedding = generate_embedding(request.query)
    semantic_results = (
        db.query(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(request.top_k*2)
        .all()
    )
    ts_query = func.plainto_tsquery("english", request.query)
    ts_vector = func.to_tsvector("english", DocumentChunk.content)
    keyword_results = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.content.match(request.query))
        .order_by(func.ts_rank(ts_vector, ts_query).desc())
        .limit(request.top_k*2)
        .all()
    )

    rrf_scores={}
    chunk_map={}
    k = 60

    for rank,chunk in enumerate(semantic_results, start = 1):
        rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0/ (k + rank)) 
        chunk_map[chunk.id] = chunk

    for rank,chunk in enumerate(keyword_results, start=1):
        rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0/ (k + rank))
        chunk_map[chunk.id] = chunk

    sorted_ids = sorted(rrf_scores.keys(), key = lambda cid:rrf_scores[cid], reverse=True)

    final_results = []
    for cid in sorted_ids[:request.top_k]:
        chunk = chunk_map[cid]
        final_results.append({
            "id": chunk.id,
            "filename": chunk.filename,
            "chunk_index" : chunk.chunk_index,
            "content": chunk.content,
            "rrf_score": round(rrf_scores[cid], 6)
        })

    set_cached_result(request.query, request.top_k, final_results)

    return {"source": "postgresql_hybrid", "results": final_results}