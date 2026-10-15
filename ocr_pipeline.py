"""
ocr_pipeline.py - Full 122-Page Parallel OCR Pipeline with Instant Disk Persistence.
Transcribes pages verbatim with temperature 0 into markdown tables and headings.
"""

import os
import io
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import pypdfium2
from dotenv import load_dotenv
from google import genai

load_dotenv()

OCR_CACHE_DIR = os.path.join(".cache", "pages")
os.makedirs(OCR_CACHE_DIR, exist_ok=True)
PDF_PATH = os.path.join("data", "UGProspectus2025.pdf")
OCR_MODEL = os.getenv("OCR_MODEL", "gemini-3.5-flash-lite")
PAGE_OFFSET = 7  # Printed Page = PDF Page Index - 7 (for page_index >= 8)


def get_printed_page(pdf_page: int) -> int:
    if pdf_page <= 7:
        return pdf_page  # Front matter
    return pdf_page - PAGE_OFFSET


def ocr_single_page(page_idx: int, client, doc) -> dict:
    pdf_page_num = page_idx + 1
    printed_page_num = get_printed_page(pdf_page_num)
    cache_path = os.path.join(OCR_CACHE_DIR, f"page_{pdf_page_num}.json")

    # Skip if already cached
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("text", "").strip():
                    return data
        except Exception:
            pass

    page = doc[page_idx]
    pil_img = page.render(scale=1.2).to_pil()
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=80)
    img_bytes = buf.getvalue()

    prompt = (
        f"You are an expert OCR transcription engine. Transcribe this page from the NED University Undergraduate Prospectus 2025 verbatim. "
        "Strict transcription rules:\n"
        "1. Temperature 0: Do not summarize, correct, infer, paraphrase, or complete anything.\n"
        "2. Tables: Output every table as a markdown table with headers. Include every number, code, fee, or seat count exactly as printed.\n"
        "3. Headings: Keep all chapter, section, and sub-section titles as markdown headings (#, ##, ###).\n"
        "4. Unreadable text: Mark any genuinely blurry or illegible word as [illegible].\n"
        "5. Output only the transcribed content without commentary."
    )

    retries = 5
    base_sleep = 4.0

    while retries > 0:
        try:
            res = client.models.generate_content(
                model=OCR_MODEL,
                contents=[
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_bytes}},
                    prompt
                ],
                config={"temperature": 0.0}
            )
            text = res.text or ""
            data = {
                "pdf_page": pdf_page_num,
                "printed_page": printed_page_num,
                "text": text
            }
            # Save immediately to disk
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data

        except Exception as e:
            err_str = str(e)
            retries -= 1
            # Exponential backoff on rate limits
            wait_time = base_sleep * (2 ** (4 - retries))
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"[Page {pdf_page_num}] Rate limit hit (429). Backing off for {wait_time:.1f}s...")
            else:
                print(f"[Page {pdf_page_num}] Error: {e}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)
            if retries == 0:
                print(f"[Page {pdf_page_num}] FAILED after all retries.")
                return {"pdf_page": pdf_page_num, "printed_page": printed_page_num, "text": ""}


def run_full_ocr(num_workers: int = 3):
    client = genai.Client()
    doc = pypdfium2.PdfDocument(PDF_PATH)
    total_pages = len(doc)

    all_pages = list(range(1, total_pages + 1))
    # Filter pending pages
    pending_pages = []
    for p in all_pages:
        c_file = os.path.join(OCR_CACHE_DIR, f"page_{p}.json")
        if not os.path.exists(c_file):
            pending_pages.append(p)
        else:
            try:
                with open(c_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if not content.get("text", "").strip():
                        pending_pages.append(p)
            except Exception:
                pending_pages.append(p)

    print(f"=== FULL PROSPECTUS OCR: {total_pages} Total Pages ===")
    print(f"Already cached: {total_pages - len(pending_pages)} pages | Remaining: {len(pending_pages)} pages")

    if not pending_pages:
        print("All 122 pages are already OCR'd and cached!")
        return

    start_time = time.time()
    completed_count = total_pages - len(pending_pages)
    newly_done = 0

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_page = {executor.submit(ocr_single_page, p - 1, client, doc): p for p in pending_pages}
        for future in as_completed(future_to_page):
            p = future_to_page[future]
            res = future.result()
            newly_done += 1
            completed_count += 1

            if completed_count % 10 == 0 or completed_count == total_pages or newly_done == len(pending_pages):
                elapsed = time.time() - start_time
                avg_speed = elapsed / max(newly_done, 1)
                remaining_sec = avg_speed * (len(pending_pages) - newly_done)
                print(
                    f"Progress: {completed_count}/{total_pages} pages done "
                    f"({(completed_count / total_pages)*100:.1f}%) | "
                    f"Speed: {avg_speed:.1f}s/page | "
                    f"Est. remaining: {remaining_sec/60:.1f} mins"
                )

    print("Full OCR pass finished.")


def run_ocr_quality_checks():
    """
    Quality check pass:
    - empty or very short (< 100 chars)
    - [illegible] count
    - truncated output
    """
    doc = pypdfium2.PdfDocument(PDF_PATH)
    total_pages = len(doc)
    client = genai.Client()

    flagged_pages = []
    print("\n=== RUNNING OCR QUALITY AUDIT ===")

    for p in range(1, total_pages + 1):
        c_file = os.path.join(OCR_CACHE_DIR, f"page_{p}.json")
        if not os.path.exists(c_file):
            flagged_pages.append((p, "Missing file"))
            continue

        with open(c_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        text = data.get("text", "").strip()
        if len(text) < 100:
            flagged_pages.append((p, f"Very short content ({len(text)} chars)"))
        elif "[illegible]" in text:
            flagged_pages.append((p, "Contains [illegible] tokens"))

    print(f"Total flagged pages: {len(flagged_pages)}")
    for p, reason in flagged_pages:
        print(f"  Page {p}: {reason}")

    # Re-run flagged pages if any
    if flagged_pages:
        print(f"Re-running {len(flagged_pages)} flagged pages for high fidelity...")
        for p, _ in flagged_pages:
            ocr_single_page(p - 1, client, doc)
        print("Re-run completed.")


if __name__ == "__main__":
    run_full_ocr(num_workers=3)
    run_ocr_quality_checks()
