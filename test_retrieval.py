"""
test_retrieval.py - Fast CLI to verify top-k chunk retrieval on the 6 competition test questions without LLM calls.
"""

import sys
from retrieve import retrieve

SIX_TEST_QUERIES = [
    ("1. Fee Question", "What is the admission and tuition fee structure for first year undergraduate programmes?"),
    ("2. Seat Question", "How many seats are allocated under different seat categories for engineering programmes?"),
    ("3. Merit/Aggregate Formula", "What is the merit formula and aggregate calculation for undergraduate admissions?"),
    ("4. Eligibility Question", "What is the minimum eligibility criteria and required percentage for Computer Systems Engineering?"),
    ("5. Regular vs Self Finance Difference", "What is the difference between seat categories and fees under Regular Scheme versus Self Finance Scheme?"),
    ("6. NOT in Prospectus (Negative Test)", "Can students pay tuition fees using cryptocurrency or Bitcoin?"),
]

def run_tests():
    print("=" * 70)
    print("RETRIEVAL VERIFICATION ON 6 CORE COMPETITION QUESTIONS")
    print("=" * 70)

    for category, query in SIX_TEST_QUERIES:
        print("\n" + "#" * 70)
        print(f"CATEGORY: {category}")
        print(f"QUERY:    {query}")
        print("#" * 70)
        try:
            chunks = retrieve(query, k=3)
            if not chunks:
                print(">>> NO CHUNKS RETRIEVED (Empty Context).")
            else:
                print(">>> RETRIEVED CHUNKS:")
                print(chunks)
        except Exception as e:
            print(f">>> Retrieval Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        custom_query = " ".join(sys.argv[1:])
        print(f"QUERY: {custom_query}\n")
        print(retrieve(custom_query, k=5))
    else:
        run_tests()
