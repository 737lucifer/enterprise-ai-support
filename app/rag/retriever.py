
import logging
import os
from math import isfinite

from app.rag.vector_store import (
    get_engine,
    get_vector_store,
)

logger = logging.getLogger(__name__)


def filter_by_distance(
    results,
    max_distance: float,
) -> list[str]:
    """Keep documents within an accepted distance."""

    evidence = []

    for doc, distance in results:
        distance = float(distance)

        source = doc.metadata.get("source", "unknown")

        logger.info(
            "RAG result source=%s distance=%.4f",
            source,
            distance,
        )

        if not isfinite(distance):
            continue

        # Smaller cosine distance means more similar.
        if distance > max_distance:
            continue

        evidence.append(
            f"Source: {source}\n"
            f"Content: {doc.page_content.strip()}"
        )

    return evidence


def search_knowledge(
    query: str,
    k: int = 3,
) -> list[str]:
    max_distance = float(
        os.getenv("RAG_MAX_DISTANCE", "0.45")
    )

    if not 0 <= max_distance <= 2:
        raise ValueError(
            "RAG_MAX_DISTANCE must be between 0 and 2"
        )

    engine = get_engine()
    store = get_vector_store(engine)

    results = store.similarity_search_with_score(
        query,
        k=k,
    )

    return filter_by_distance(
        results,
        max_distance,
    )
