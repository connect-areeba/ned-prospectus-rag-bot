import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_api_key_here":
    print("ERROR: GEMINI_API_KEY is not set in .env file.")
    print("Please create or edit .env and set GEMINI_API_KEY=your_key")
    sys.exit(1)

from google import genai

client = genai.Client()

print("=== Fetching Available Models via client.models.list() ===")
models_list = list(client.models.list())
for m in models_list:
    name = getattr(m, "name", str(m))
    display_name = getattr(m, "display_name", "")
    methods = getattr(m, "supported_actions", []) or getattr(m, "supported_generation_methods", [])
    if "flash" in name.lower() or "embed" in name.lower():
        print(f"Model: {name} | Display: {display_name}")

print("\n=== Testing Generation Model ===")
# Candidate chat models in priority order
chat_candidates = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
selected_chat = None

for model_name in chat_candidates:
    try:
        print(f"Testing chat model '{model_name}'...")
        res = client.models.generate_content(
            model=model_name,
            contents="Say 'OK' if you can read this.",
        )
        print(f"SUCCESS: {model_name} responded: {res.text.strip()}")
        selected_chat = model_name
        break
    except Exception as e:
        print(f"FAILED {model_name}: {e}")

print("\n=== Testing Embedding Model ===")
# Candidate embedding models in priority order
embedding_candidates = ["gemini-embedding-001", "text-embedding-004"]
selected_embed = None

for model_name in embedding_candidates:
    try:
        print(f"Testing embedding model '{model_name}'...")
        res = client.models.embed_content(
            model=model_name,
            contents="Testing embedding connection.",
        )
        dims = len(res.embeddings[0].values) if res.embeddings else 0
        print(f"SUCCESS: {model_name} returned embedding of dimension {dims}")
        selected_embed = model_name
        break
    except Exception as e:
        print(f"FAILED {model_name}: {e}")

print("\n=== FINAL TEST SUMMARY ===")
print(f"Selected Chat Model: {selected_chat}")
print(f"Selected Embedding Model: {selected_embed}")
