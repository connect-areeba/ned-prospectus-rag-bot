"""
retrieve.py - Top-k similarity search on persistent vector store.
Formats retrieved chunks as: [Page N, Section X] text
where N is the printed page number from the prospectus.
Reads EMBED_MODEL and DB from environment.
"""

import os
from dotenv import load_dotenv
from google import genai
from vector_store import LocalVectorStore

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
_vector_store = None
_genai_client = None


def get_genai_client():
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client()
    return _genai_client


def get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = LocalVectorStore()
    return _vector_store


def embed_query(query: str):
    client = get_genai_client()
    res = client.models.embed_content(
        model=EMBED_MODEL,
        contents=query,
    )
    return res.embeddings[0].values


def retrieve(query: str, k: int = 5) -> str:
    """
    Performs top-k vector similarity search for the user query.
    Returns concatenated formatted string of chunks:
    [Page N, Section X]
    chunk text...
    where N is the printed page number.
    """
    try:
        vs = get_vector_store()
    except Exception as e:
        print(f"Warning: Could not open vector store: {e}")
        return ""

    query_vec = embed_query(query)
    documents, metadatas, scores = vs.query(query_vec, top_k=k)

    formatted_chunks = []
    for doc, meta in zip(documents, metadatas):
        # We prioritize printed_page as requested: "so it matches what a student sees in the prospectus"
        printed_page = meta.get("printed_page", meta.get("page", "?"))
        section = meta.get("section", "General")
        header = f"[Page {printed_page}, Section {section}]"
        formatted_chunks.append(f"{header}\n{doc}")

    return "\n\n".join(formatted_chunks)
