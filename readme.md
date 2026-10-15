# NED Undergraduate Prospectus 2025 RAG Chatbot
**Module 1: "The Engineer's Code" Competition**

An end-to-end grounded Retrieval-Augmented Generation (RAG) assistant for NED University of Engineering & Technology (Karachi, Pakistan). Designed to enforce strict grounding, preserve a calm and professional senior-student persona under prompt manipulation, and explicitly refuse out-of-scope inquiries.

---

## 📋 System Requirements & Compliance

| Requirement | Implementation & Defense |
|---|---|
| **Strict Grounding** | Answers derived exclusively from `data/UGProspectus2025.pdf` via verbatim Gemini OCR cache (all 122 pages). Never invents figures, fees, or policies. Includes printed page citations `[Page N, Section X]` with the +7 offset. |
| **Tone Preservation & Defense** | Enforces the system prompt specifications: warm, calm, and senior-student persona. Tested against jailbreaks, insults, DAN mode, and prompt leakage. |
| **Out-of-Scope Refusal** | Refuses general knowledge, non-NED queries, homework, coding, and crypto inquiries using the official fallback prompt. |
| **SDK & Stack** | Built with official `google-genai` Python SDK, SQLite3 vector store with cosine similarity, and Streamlit frontend. |
| **Multi-Turn Query Rewriting** | Conversation context synthesis in `app.py` resolves pronouns and follow-up queries into standalone search targets. |

---

## ⚡ Quick Start & Operational Run Instructions

### 1. Prerequisites & Environment Setup
Ensure Python 3.10+ is installed. Install dependencies from the manifest:
```bash
py -m pip install -r requirements.txt
```

### 2. Configure Your API Key
Copy the example environment file and insert your Google AI Studio API key:
```bash
# On Windows PowerShell / CMD:
copy .env.example .env

# On Linux / macOS:
cp .env.example .env
```
Inside `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
CHAT_MODEL=gemini-3.5-flash-lite
EMBED_MODEL=gemini-embedding-001
```

### 3. Verify Model Connection
Confirm API key validity and SDK connection:
```bash
py test_connection.py
```

### 4. Build or Verify Vector Index
The repository includes the cached verbatim OCR text (`.cache/pages/`) and vector database. To re-index or verify:
```bash
py ingest.py
```

### 5. Run Automated Benchmark Evaluation
Run the automated evaluation harness against the competition's 6 benchmark questions (Fee structure, BCIT seats, Merit formula, CSE eligibility, Regular vs Self-Finance, and Crypto refusal):
```bash
py run_evaluation.py
```

### 6. Launch the Streamlit Chat Assistant
Start the interactive UI on `http://localhost:8501`:
```bash
py -m streamlit run app.py
```

---

## 🏛️ System Architecture

1. **Extraction & OCR (`ocr_pipeline.py`):**
   - 100% of the 122 scanned prospectus pages extracted verbatim at temperature 0 via Gemini Vision OCR.
   - 241 tables converted to self-contained rows with repeated headers across multi-page table splits.
2. **Vector Index & Storage (`vector_store.py` & `ingest.py`):**
   - 349 structure-aware chunks embedded with `gemini-embedding-001` (3,072 dimensions).
   - Stored in persistent local vector database (`chroma_db/vector_store.db`).
3. **Retrieval Engine (`retrieve.py`):**
   - Top-$k$ Cosine Similarity search with printed page mapping (`Printed Page = PDF Page - 7` for $p \ge 8$).
4. **Inference Pipeline (`ask.py` & `systemprompt.txt`):**
   - Strict `str.replace("{context}", ...)` context injection into `systemprompt.txt`.
5. **UI & Styling (`app.py`):**
   - Aesthetically refined organic theme: `#FEF9EB` warm beige background, `#304D6D` dusk blue text, `#A6BED4` cylindrical message bubbles, and drawer toggle.

---

## 📦 Deliverables & Repository Structure

```text
├── app.py                 # Streamlit chat interface with custom CSS styling
├── ask.py                 # CLI inference pipeline using google-genai SDK
├── retrieve.py            # Top-k vector retrieval with page offset mapping
├── ingest.py              # Prospectus chunking and vector store builder
├── vector_store.py        # Local vector database engine with cosine similarity
├── ocr_pipeline.py        # Gemini Vision OCR pipeline for scanned PDF
├── run_evaluation.py      # Automated benchmark evaluation suite
├── test_connection.py     # Connection test script for Google AI Studio
├── systemprompt.txt       # Unmodified official competition system prompt
├── requirements.txt       # Reproducible dependency manifest
├── DEFENSE.md             # 1-Minute oral defense script and technical specifications
├── .env.example           # Environment template (API key placeholder)
└── assets/                # UI icons and branding assets
```
