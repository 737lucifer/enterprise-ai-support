
from langchain_core.documents import Document

from app.rag.retriever import filter_by_distance


def test_retrieval_filters_irrelevant_documents():
    results = [
        (
            Document(
                page_content="Candidate sync API failure",
                metadata={"source": "INC001"},
            ),
            0.15,
        ),
        (
            Document(
                page_content="SSO certificate expired",
                metadata={"source": "INC002"},
            ),
            0.72,
        ),
    ]

    evidence = filter_by_distance(
        results,
        max_distance=0.45,
    )

    assert len(evidence) == 1
    assert "INC001" in evidence[0]
    assert "INC002" not in evidence[0]


def test_no_relevant_documents():
    results = [
        (
            Document(
                page_content="Unrelated incident",
                metadata={"source": "INC999"},
            ),
            0.85,
        )
    ]

    evidence = filter_by_distance(
        results,
        max_distance=0.45,
    )

    assert evidence == []
