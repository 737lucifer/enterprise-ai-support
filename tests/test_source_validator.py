
from app.agents.source_validator import validate_sources


def test_valid_source():
    evidence = [
        "Source: INC001\nContent: API integration issue"
    ]

    result = validate_sources(
        evidence,
        ["INC001"],
    )

    assert result == ["INC001"]


def test_fake_source_removed():
    evidence = [
        "Source: INC001\nContent: API integration issue"
    ]

    result = validate_sources(
        evidence,
        ["INC999"],
    )

    assert result == []


def test_mixed_sources():
    evidence = [
        "Source: INC001\nContent: Integration failure",
        "Source: INC002\nContent: Authentication failure",
    ]

    result = validate_sources(
        evidence,
        ["INC001", "FAKE123", "INC002"],
    )

    assert result == ["INC001", "INC002"]


def test_no_evidence():
    assert validate_sources([], ["INC001"]) == []
