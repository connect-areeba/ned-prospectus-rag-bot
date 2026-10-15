"""
ask.py - End-to-end question answering pipeline for NED Guide.
Reads systemprompt.txt without modification, populates {context} using str.replace,
and queries Gemini Flash via the official google-genai SDK.
"""

import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from retrieve import retrieve

load_dotenv()

CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-3.8-flash")
SYSTEM_PROMPT_PATH = "systemprompt.txt"

_client = None


def get_genai_client():
    global _client
    if _client is None:
        _client = genai.Client()
    return _client


def load_system_prompt_with_context(context_text: str) -> str:
    """
    Loads systemprompt.txt and replaces {context} with retrieved context strictly
    using str.replace("{context}", ...). Never modifies the underlying prompt file.
    """
    if not os.path.exists(SYSTEM_PROMPT_PATH):
        raise FileNotFoundError(f"System prompt file not found: {SYSTEM_PROMPT_PATH}")

    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    # Strict str.replace requirement
    return template.replace("{context}", context_text)


def ask_question(question: str, k: int = 4) -> str:
    """
    Performs vector retrieval, builds the grounded prompt, and calls Gemini Flash.
    """
    client = get_genai_client()

    # 1. Retrieve top-k chunks
    retrieved_context = retrieve(question, k=k)

    # 2. Inject context into system prompt
    full_system_instruction = load_system_prompt_with_context(retrieved_context)

    # 3. Generate response with automatic failover across active models
    fallback_models = [CHAT_MODEL, "gemini-3.7-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]
    seen = set()
    ordered_models = []
    for m in fallback_models:
        if m and m not in seen:
            seen.add(m)
            ordered_models.append(m)

    last_err = None
    for m in ordered_models:
        try:
            response = client.models.generate_content(
                model=m,
                contents=question,
                config=types.GenerateContentConfig(
                    system_instruction=full_system_instruction,
                    temperature=0.1,
                )
            )
            return response.text
        except Exception as e:
            last_err = e
            continue

    raise last_err


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Ask NED Guide a question about the Undergraduate Prospectus 2025:\n> ")

    print("\nRetrieving knowledge and generating answer...")
    answer = ask_question(query)
    print("\n" + "=" * 60)
    print("NED GUIDE RESPONSE:")
    print("=" * 60)
    print(answer)