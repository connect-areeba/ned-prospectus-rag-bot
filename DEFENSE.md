# Module 1: "The Engineer's Code" — NED University RAG Bot Defense Document

## 1. Executive Summary & Architecture Overview
This pipeline implements an end-to-end, competition-grade Retrieval-Augmented Generation (RAG) system for the **NED University Undergraduate Prospectus 2025** (`data/UGProspectus2025.pdf`).

```
[UGProspectus2025.pdf (122 Scanned Pages)]
                   │
                   ▼ (pypdfium2 @ 1.2x scale)
[Page Images rendered to disk]
                   │
                   ▼ (Google Gemini Vision OCR - Verbatim, temp=0, markdown tables)
[.cache/pages/page_{1..122}.json]
                   │
                   ▼ (Table Restructuring: Repeated headers per row & multi-page carryover)
[Structure-Aware Chunker (~1800 chars / 350 overlap, Chapter/Section awareness)]
                   │
                   ▼ (gemini-embedding-001 with sha256 disk cache)
[chroma_db/vector_store.db (Zero-dependency SQLite3 + NumPy Cosine Engine)]
                   │
                   ▼ (Cosine Similarity Top-K Retrieval)
[Prompt Injection: str.replace("{context}", ...) in systemprompt.txt]
                   │
                   ▼ (Google Gemini Flash with Exponential Backoff)
[Streamlit Chat UI + Python CLI (ask.py)]
```

---

## 2. Key Engineering Decisions & Competition Safeguards

### A. Document Reality: 100% Scanned Raster
- Digital text extraction via standard libraries (`pdfplumber`, `pypdf`) extracted **0 characters** across all 122 pages.
- **Solution:** Rendered high-fidelity page images and performed zero-temperature verbatim OCR using Google Gemini Multimodal Vision, preserving headings, bolding, and complex admissions tables.
- Cached page-by-page as atomic JSON documents in `.cache/pages/` so processing is idempotent and resumable.

### B. Page Offset Calibration
- **Discovery:** Front matter, foreword, and table of contents occupy PDF pages 1–7.
- **Printed Page 1** begins at **PDF Page 8**.
- **Offset = 7** (`Printed Page = PDF Page Index - 7` for $p \ge 8$).
- Both `pdf_page` and `printed_page` are retained in chunk metadata. Citations strictly output `[Page N, Section X]` where `N` matches what a student or evaluator reads in the printed prospectus.

### C. Multi-Column & Cross-Page Table Preservation
- NED seat distribution tables (Regular R-series & Self-Finance SF-series) span across 30+ columns and consecutive landscape pages.
- **Ingestion Transform:** Markdown table blocks are converted into self-contained row statements where column headers (program codes like CE, ME, CS) and sub-category rows (boards) are paired into explicit key-value sentences.
- Header states are carried forward across page boundaries to prevent orphaned numbers.

### D. Zero-Compromise Embeddings & Storage
- **Embedding Model:** Google `gemini-embedding-001` producing 3072-dimensional semantic embeddings.
- **Cache:** Hash-keyed `.cache/embeddings_cache.json` guarantees zero redundant API spend or rate quota consumption during re-runs.
- **Vector Store:** Implemented via standard-library `sqlite3` + `numpy` (`LocalVectorStore`), bypassing Windows Python 3.14 C++ compilation wheel bottlenecks while providing instant top-$k$ cosine search.

### E. Prompt Integrity & Hallucination Defense
- `systemprompt.txt` is loaded as a fixed template; retrieved context is injected strictly using `str.replace("{context}", ...)`.
- Model strictly adheres to system prompt directives:
  - Answers only from provided context.
  - Generates exact citations: `(p. 71, sec. 4.4.1)`.
  - Asks clarifying questions when user intent is ambiguous (e.g., asking if user refers to Regular or Self-Finance scheme for fees).
  - Cleanly triggers fallback for out-of-scope/negative questions (e.g., cryptocurrency/Bitcoin payments).
  - Appends admissions office confirmation disclaimer on quantitative figures.

---

## 3. Benchmark Evaluation Results (6 Core Test Queries)

| # | Question Category | Query | Bot Response Summary & Citation | Pass? |
|---|-------------------|-------|---------------------------------|:-----:|
| 1 | **Fee Structure** | *What is the admission and tuition fee structure for first year undergraduate programmes?* | System detected ambiguity between schemes and campuses per prompt rule 6, asking the student to clarify whether they mean Regular vs Self-Finance or Main Campus vs TIEST. | ✅ PASS |
| 2 | **Seat Distribution** | *How many seats are allocated under different seat categories for engineering programmes?* | Correctly cited `Section 5.1(i), p. 73` (R-1(a) Karachi Board: 105 Civil, 22 Mechanical, 56 CS, 1464 total) and `Section 5.2(i), pp. 79-80` for Self-Finance. | ✅ PASS |
| 3 | **Merit Formula** | *What is the merit formula and aggregate calculation for undergraduate admissions?* | Output exact formula: $\text{Merit Score} = 40\% \text{ (HSC-I/O-Level)} + 60\% \text{ Entry Test Score}$. Detailed foreign equivalency, Hafiz-e-Quran (+1.82%), and improvement deduction (-0.91%) citing `p. 71, sec. 4.4.1`. | ✅ PASS |
| 4 | **Eligibility** | *What is the minimum eligibility criteria and required percentage for Computer Systems Engineering?* | Stated Sindh domicile, 60% aggregate minimum (57% for HSC-I waiting), Pre-Engineering subjects or Math/Physics/CS with additional Chemistry NC course. Cited `p. 70, sec. 4.2`. | ✅ PASS |
| 5 | **Regular vs Self-Finance** | *What is the difference between seat categories and fees under Regular Scheme versus Self Finance Scheme?* | Contrasted R-categories vs Self-Finance fee tiers: SF-1 to SF-5 (Rs. 855,000/-) and SF-6 to SF-11 (Rs. 1,065,000/-) citing `p. 93`. | ✅ PASS |
| 6 | **Negative / Out-of-Scope** | *Can students pay tuition fees using cryptocurrency or Bitcoin?* | Exact prompt fallback response: *"I couldn't find that in the NED Undergraduate Prospectus 2025, so I don't want to guess..."* Zero hallucination. | ✅ PASS |

---

## 4. How to Run

### Command Line Evaluation
```bash
# Run similarity retrieval test on all 6 questions
py test_retrieval.py

# Run full end-to-end RAG answers on all 6 questions
py run_evaluation.py

# Ask an ad-hoc question
py ask.py "What are the hostel charges?"
```

### Streamlit Web UI
```bash
py -m streamlit run app.py
```
*Access via browser at `http://localhost:8501`.*
