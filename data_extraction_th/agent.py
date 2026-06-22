"""Agente RAG multimodal: recupera as páginas top-k do vector store e gera
uma resposta embasada nas páginas (PDF como contexto), com links de citação
no formato `arquivo.pdf#page=N`.

Uso típico no notebook:

    from agent import answer_question
    resposta = answer_question(
        vector_store,
        client,
        "Quais são os sintomas de hipoglicemia?",
        source="Livro_GuiaRapido-DiabetesMellitus_PDFDigital_20231113.pdf",
        k=3,
    )
    print(resposta.as_markdown())
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

from google import genai
from google.genai import types
from langchain_chroma import Chroma
from pypdf import PdfReader, PdfWriter


SYSTEM_PROMPT = (
    "Você é um assistente clínico que responde com base APENAS nas páginas de "
    "guias rápidos de saúde anexadas. Para cada afirmação importante, cite as "
    "páginas no formato (pág. N). Se a resposta não estiver nas páginas "
    "fornecidas, diga isso explicitamente. Responda em português, de forma "
    "clara e objetiva."
)


@dataclass
class Source:
    source: str
    path: str
    page: int
    score: float


@dataclass
class AnswerWithSources:
    answer: str
    sources: list[Source] = field(default_factory=list)

    def as_markdown(self) -> str:
        if not self.sources:
            return self.answer
        cites = "\n".join(
            f"- [{s.source} — pág. {s.page}]({s.path}#page={s.page})"
            f"  (score={s.score:.4f})"
            for s in self.sources
        )
        return f"{self.answer}\n\n**Fontes:**\n{cites}"


def _get_page_bytes(pdf_path: str, page_num: int) -> bytes:
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.add_page(reader.pages[page_num - 1])
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def answer_question(
    vector_store: Chroma,
    client: genai.Client,
    pergunta: str,
    source: str | None = None,
    k: int = 3,
    model: str = "gemini-2.5-flash",
) -> AnswerWithSources:
    """Responde a `pergunta` usando as `k` páginas mais relevantes.

    1. Busca semântica no `vector_store` (opcionalmente filtrada por `source`).
    2. Anexa cada página recuperada como PDF ao prompt do Gemini (multimodal).
    3. Gera a resposta e retorna junto com as fontes citáveis.
    """
    filtro = {"source": source} if source else None
    hits = vector_store.similarity_search_with_score(pergunta, k=k, filter=filtro)

    if not hits:
        return AnswerWithSources(answer="Nenhuma página relevante encontrada.")

    parts: list = [
        f"Pergunta: {pergunta}\n\nResponda com base apenas nas páginas anexadas."
    ]
    sources: list[Source] = []

    for doc, score in hits:
        meta = doc.metadata
        parts.append(
            types.Part.from_bytes(
                data=_get_page_bytes(meta["path"], meta["page"]),
                mime_type="application/pdf",
            )
        )
        sources.append(
            Source(
                source=meta["source"],
                path=meta["path"],
                page=meta["page"],
                score=float(score),
            )
        )

    resp = client.models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    return AnswerWithSources(answer=resp.text or "", sources=sources)
