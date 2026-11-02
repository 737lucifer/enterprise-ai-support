
import re

SOURCE_PATTERN = re.compile(
    r"^Source:\s*(.+)$",
    re.MULTILINE,
)


def validate_sources(
    evidence: list[str],
    claimed_sources: list[str],
) -> list[str]:
    """Return only source IDs present in retrieved evidence."""

    allowed = set()

    for document in evidence:
        match = SOURCE_PATTERN.search(document)

        if match:
            allowed.add(match.group(1).strip())

    return list(dict.fromkeys(
        source for source in claimed_sources
        if source in allowed
    ))
