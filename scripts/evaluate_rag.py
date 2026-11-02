
import os
from dotenv import load_dotenv

from app.rag.retriever import search_knowledge

load_dotenv()

# Known sample incidents and their expected sources
test_cases = [
    {
        "query": "Candidate synchronization API returns HTTP 500",
        "expected": "INC001",
    },
    {
        "query": "Users cannot log in due to expired SSO certificate",
        "expected": "INC002",
    },
    {
        "query": "Database connection pool is exhausted",
        "expected": "RB003",
    },
]


def evaluate():
    passed = 0

    for index, case in enumerate(test_cases, start=1):
        print(f"\nTest {index}: {case['query']}")

        evidence = search_knowledge(
            query=case["query"],
            k=3,
        )

        retrieved_sources = []

        for item in evidence:
            source = item.split("\n")[0].replace(
                "Source: ", ""
            )
            retrieved_sources.append(source)

        correct = case["expected"] in retrieved_sources

        print("Expected:", case["expected"])
        print("Retrieved:", retrieved_sources)
        print("Result:", "PASS" if correct else "FAIL")

        if correct:
            passed += 1

    accuracy = passed / len(test_cases) * 100

    print("\n------------------------")
    print(f"Retrieval Hit Rate@3: {accuracy:.1f}%")
    print(f"Passed: {passed}/{len(test_cases)}")


if __name__ == "__main__":
    evaluate()
