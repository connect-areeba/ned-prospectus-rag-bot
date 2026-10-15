"""
run_evaluation.py - Executes the full RAG pipeline (Retrieval + LLM Answer Generation)
on the 6 competition test questions and prints complete answers with citations.
"""

from ask import ask_question

SIX_TEST_QUERIES = [
    ("1. Fee Question", "What is the admission and tuition fee structure for first year undergraduate programmes?"),
    ("2. Seat Question", "How many seats are allocated under different seat categories for engineering programmes?"),
    ("3. Merit/Aggregate Formula", "What is the merit formula and aggregate calculation for undergraduate admissions?"),
    ("4. Eligibility Question", "What is the minimum eligibility criteria and required percentage for Computer Systems Engineering?"),
    ("5. Regular vs Self Finance Difference", "What is the difference between seat categories and fees under Regular Scheme versus Self Finance Scheme?"),
    ("6. Negative Test (NOT in Prospectus)", "Can students pay tuition fees using cryptocurrency or Bitcoin?"),
]

def main():
    print("=" * 80)
    print("COMPETITION EVALUATION: END-TO-END RAG PIPELINE (NED GUIDE)")
    print("=" * 80)

    for i, (cat, q) in enumerate(SIX_TEST_QUERIES, 1):
        print(f"\n[{i}/6] CATEGORY: {cat}")
        print(f"QUESTION: {q}")
        print("-" * 80)
        try:
            answer = ask_question(q)
            print(answer)
        except Exception as e:
            print(f"Error: {e}")
        print("=" * 80)

if __name__ == "__main__":
    main()
