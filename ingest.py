"""
ingest.py - Loads cached OCR pages, transforms tables into self-contained row representations,
chunks documents with structure and page awareness, embeds with gemini-embedding-001,
and persists chunks and vectors into LocalVectorStore.
"""

import os
import re
import json
import time
import hashlib
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
CACHE_DIR = ".cache"
PAGES_DIR = os.path.join(CACHE_DIR, "pages")
CACHE_FILE = os.path.join(CACHE_DIR, "embeddings_cache.json")

os.makedirs(CACHE_DIR, exist_ok=True)


def parse_markdown_table_to_rows(table_lines: List[str], carried_headers: List[str] = None) -> Tuple[List[str], List[str]]:
    """
    Parses a markdown table into self-contained descriptive rows where each column header is repeated.
    Carries headers across pages if table continues.
    """
    if not table_lines:
        return [], carried_headers

    cleaned = [line.strip() for line in table_lines if line.strip()]
    if not cleaned:
        return [], carried_headers

    headers = []
    start_row = 0

    # Look for header and separator
    for i in range(min(5, len(cleaned))):
        row = cleaned[i]
        if "|" in row:
            cells = [c.strip() for c in row.split("|")[1:-1]] if row.startswith("|") and row.endswith("|") else [c.strip() for c in row.split("|")]
            # Check if this or next is separator
            if any(set(c.replace(":", "").replace("-", "")) == set() for c in cells if c):
                # This is separator line
                if i > 0:
                    prev_cells = [c.strip() for c in cleaned[i-1].split("|")[1:-1]] if cleaned[i-1].startswith("|") and cleaned[i-1].endswith("|") else [c.strip() for c in cleaned[i-1].split("|")]
                    headers = [c for c in prev_cells if c]
                    start_row = i + 1
                    break

    if not headers and carried_headers:
        headers = carried_headers
        start_row = 0

    if not headers:
        # Fallback: treat as raw text
        return cleaned, None

    row_sentences = []
    category_context = ""

    for line in cleaned[start_row:]:
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]] if line.startswith("|") and line.endswith("|") else [c.strip() for c in line.split("|")]
        # Remove empty boundary cells
        non_empty = [c for c in cells if c]
        if not non_empty:
            continue
        # Skip if separator row
        if all(set(c.replace(":", "").replace("-", "")) == set() for c in non_empty):
            continue

        # If it's a category header row spanning across (e.g. bold category name followed by blank cells)
        if len(non_empty) == 1 and non_empty[0].startswith("**"):
            category_context = non_empty[0].replace("**", "").strip()
            continue

        # Pair cells with headers
        pairs = []
        if category_context:
            pairs.append(f"Sub-Category/Board: {category_context}")

        for h, v in zip(headers, cells):
            if h and v and v != "-":
                pairs.append(f"{h}: {v}")

        if pairs:
            row_sentences.append(" | ".join(pairs))

    return row_sentences, headers


def process_page_tables_and_text(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transforms markdown tables in pages into self-contained repeated-header rows,
    carrying headers over across consecutive table continuation pages.
    """
    processed_pages = []
    carried_headers = None
    table_count = 0

    for p in pages:
        text = p["text"]
        lines = text.split("\n")
        new_lines = []
        table_buffer = []
        in_table = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and "|" in stripped[1:]:
                in_table = True
                table_buffer.append(stripped)
            else:
                if in_table and table_buffer:
                    rows, headers = parse_markdown_table_to_rows(table_buffer, carried_headers)
                    if rows:
                        new_lines.append("\n[Table Content (Structured Rows)]:\n" + "\n".join(rows) + "\n")
                        table_count += 1
                    carried_headers = headers
                    table_buffer = []
                    in_table = False
                new_lines.append(line)

        if in_table and table_buffer:
            rows, headers = parse_markdown_table_to_rows(table_buffer, carried_headers)
            if rows:
                new_lines.append("\n[Table Content (Structured Rows)]:\n" + "\n".join(rows) + "\n")
                table_count += 1
            carried_headers = headers
        else:
            # If page did not end with a table, reset carried headers unless next page clearly starts with table
            pass

        processed_pages.append({
            "pdf_page": p["pdf_page"],
            "printed_page": p["printed_page"],
            "text": "\n".join(new_lines)
        })

    print(f"Preserved and converted {table_count} table sections across all pages.")
    return processed_pages


def chunk_document_structure_aware(pages_data: List[Dict[str, Any]], target_chars: int = 1800, overlap_chars: int = 350) -> List[Dict[str, Any]]:
    chunks = []
    heading_regex = re.compile(r"^(#+\s+.*|CHAPTER\s+\d+|SECTION\s+\d+|[0-9]+(\.[0-9]+)+\s+.*|[A-Z\s]{4,}:?$)", re.MULTILINE)
    current_section = "General Prospectus Information"

    for page_item in pages_data:
        pdf_page = page_item["pdf_page"]
        printed_page = page_item["printed_page"]
        page_text = page_item["text"]
        paragraphs = re.split(r"\n\s*\n", page_text)

        current_buffer = []
        current_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            first_line = para.split("\n")[0].strip()
            if heading_regex.match(first_line) and len(first_line) < 100:
                current_section = first_line.replace("#", "").strip()

            if current_len + len(para) > target_chars and current_buffer:
                chunk_text = "\n\n".join(current_buffer)
                chunks.append({
                    "text": chunk_text,
                    "pdf_page": pdf_page,
                    "printed_page": printed_page,
                    "section": current_section
                })
                overlap_text = current_buffer[-1] if len(current_buffer[-1]) < overlap_chars else current_buffer[-1][-overlap_chars:]
                current_buffer = [overlap_text, para]
                current_len = sum(len(p) for p in current_buffer)
            else:
                current_buffer.append(para)
                current_len += len(para)

        if current_buffer:
            chunk_text = "\n\n".join(current_buffer)
            chunks.append({
                "text": chunk_text,
                "pdf_page": pdf_page,
                "printed_page": printed_page,
                "section": current_section
            })

    return chunks


def load_cache() -> Dict[str, List[float]]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, List[float]]):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def embed_chunks_batched(client, chunks: List[Dict[str, Any]], batch_size: int = 15) -> List[List[float]]:
    cache = load_cache()
    embeddings = []
    to_embed_indices = []

    for idx, c in enumerate(chunks):
        content = c["text"]
        chunk_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        c["hash"] = chunk_hash
        if chunk_hash in cache:
            embeddings.append(cache[chunk_hash])
        else:
            embeddings.append(None)
            to_embed_indices.append(idx)

    print(f"Total chunks: {len(chunks)}. Found in cache: {len(chunks) - len(to_embed_indices)}. Need embedding: {len(to_embed_indices)}.")

    for i in range(0, len(to_embed_indices), batch_size):
        batch_slice = to_embed_indices[i : i + batch_size]
        batch_texts = [chunks[idx]["text"] for idx in batch_slice]

        print(f"Embedding batch {i // batch_size + 1} / {(len(to_embed_indices) + batch_size - 1) // batch_size} ({len(batch_texts)} chunks)...")

        retries = 5
        while retries > 0:
            try:
                batch_vectors = []
                for text in batch_texts:
                    res = client.models.embed_content(
                        model=EMBED_MODEL,
                        contents=text,
                    )
                    batch_vectors.append(res.embeddings[0].values)
                    time.sleep(0.1)

                for chunk_idx, vector in zip(batch_slice, batch_vectors):
                    embeddings[chunk_idx] = vector
                    cache[chunks[chunk_idx]["hash"]] = vector

                save_cache(cache)
                break
            except Exception as e:
                retries -= 1
                wait_time = (6 - retries) * 5
                print(f"Error during embedding batch: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                if retries == 0:
                    raise RuntimeError(f"Failed to embed batch: {e}")

    return embeddings


def build_index():
    print("=== Starting Ingestion Pipeline for NED Undergraduate Prospectus 2025 ===")
    from google import genai
    client = genai.Client()

    # 1. Read all cached OCR pages
    pages = []
    for i in range(1, 123):
        path = os.path.join(PAGES_DIR, f"page_{i}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing cached page: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            pdf_p = data.get("pdf_page", data.get("page", data.get("page_number", i)))
            printed_p = data.get("printed_page", max(1, pdf_p - 7) if pdf_p >= 8 else pdf_p)
            pages.append({
                "pdf_page": pdf_p,
                "printed_page": printed_p,
                "text": data.get("text", "")
            })

    print(f"Loaded all {len(pages)} OCR pages from {PAGES_DIR}.")

    # 2. Table transformations with header carrying
    processed_pages = process_page_tables_and_text(pages)

    # 3. Structure-aware chunking
    chunks = chunk_document_structure_aware(processed_pages)
    print(f"Created {len(chunks)} structure-aware chunks.")

    # 4. Batched embedding
    vectors = embed_chunks_batched(client, chunks)

    # 5. Save into LocalVectorStore
    try:
        from vector_store import LocalVectorStore
        vs = LocalVectorStore()
        vs.reset()
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        documents = [c["text"] for c in chunks]
        metadatas = [
            {
                "pdf_page": c["pdf_page"],
                "printed_page": c["printed_page"],
                "section": c["section"]
            }
            for c in chunks
        ]
        vs.add(ids, documents, metadatas, vectors)
        print(f"SUCCESS: Indexed {len(chunks)} chunks into LocalVectorStore at chroma_db/vector_store.db")
    except Exception as e:
        print(f"Error saving to vector store: {e}")
        raise e


if __name__ == "__main__":
    build_index()
