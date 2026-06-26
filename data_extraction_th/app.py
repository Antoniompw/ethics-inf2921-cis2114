from fastapi import FastAPI, HTTPException
from app_models import *


from langchain_chroma import Chroma

vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
)




app = FastAPI(title="Guia Rápido RAG")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "vectors_indexed": count()}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    if count() == 0:
        raise HTTPException(
            status_code=503,
            detail="Coleção vazia. Rode o pipeline do notebook.",
        )
    hits = retrieve(req.question, req.source, req.k)
    answer = generate_answer(req.question, hits)
    return AskResponse(
        answer=answer,
        citations=[
            Citation(
                source=doc.metadata["source"],
                page=int(doc.metadata["page"]),
                distance=float(score),
            )
            for doc, score in hits
        ],
    )
