"""Claim extractor tests."""

import pytest

from app.pipeline.claim_extractor import ClaimExtractor


@pytest.fixture
def extractor() -> ClaimExtractor:
    return ClaimExtractor()


@pytest.mark.asyncio
async def test_extracts_two_python_sentences(extractor: ClaimExtractor) -> None:
    answer = (
        "Python was created by Guido van Rossum. "
        "Python 1.0 was released in 1994."
    )
    claims = await extractor.extract(answer)

    assert len(claims) == 2
    assert claims[0].id == "claim_1"
    assert claims[1].id == "claim_2"
    assert claims[0].text == "Python was created by Guido van Rossum."
    assert claims[1].text == "Python 1.0 was released in 1994."
    assert claims[0].type == "factual"
    assert claims[1].type == "date"


@pytest.mark.asyncio
async def test_ignores_empty_and_punctuation_only_sentences(
    extractor: ClaimExtractor,
) -> None:
    claims = await extractor.extract("The sky is blue. .   !  Water is wet.")
    assert [claim.text for claim in claims] == [
        "The sky is blue.",
        "Water is wet.",
    ]
    assert [claim.id for claim in claims] == ["claim_1", "claim_2"]


@pytest.mark.asyncio
async def test_classifies_numerical_claims(extractor: ClaimExtractor) -> None:
    claims = await extractor.extract("The package contains 42 items.")
    assert len(claims) == 1
    assert claims[0].type == "numerical"


@pytest.mark.asyncio
async def test_assigns_unknown_for_short_non_numeric_text(
    extractor: ClaimExtractor,
) -> None:
    claims = await extractor.extract("Yes.")
    assert len(claims) == 1
    assert claims[0].type == "unknown"


@pytest.mark.asyncio
async def test_keeps_abbreviations_and_decimals_in_one_claim(
    extractor: ClaimExtractor,
) -> None:
    claims = await extractor.extract(
        "Dr. Smith joined the U.S. Navy. Python 1.0 shipped in 1994."
    )
    assert [claim.text for claim in claims] == [
        "Dr. Smith joined the U.S. Navy.",
        "Python 1.0 shipped in 1994.",
    ]
    assert claims[0].type == "factual"
    assert claims[1].type == "date"


@pytest.mark.asyncio
async def test_splits_semicolons_and_contrast_clauses(
    extractor: ClaimExtractor,
) -> None:
    claims = await extractor.extract(
        "Paris is the capital of France; Lyon is a major city. "
        "The first iPhone launched in June 2007 but the announcement was in January 2007."
    )
    assert [claim.text for claim in claims] == [
        "Paris is the capital of France.",
        "Lyon is a major city.",
        "The first iPhone launched in June 2007.",
        "The announcement was in January 2007.",
    ]
    assert claims[2].type == "date"
    assert claims[3].type == "date"


@pytest.mark.asyncio
async def test_skips_interrogative_sentences(extractor: ClaimExtractor) -> None:
    claims = await extractor.extract(
        "When was the first iPhone released? The first iPhone was released in 2007."
    )
    assert [claim.text for claim in claims] == [
        "The first iPhone was released in 2007.",
    ]


@pytest.mark.asyncio
async def test_splits_paragraph_breaks(extractor: ClaimExtractor) -> None:
    claims = await extractor.extract(
        "Python was created by Guido van Rossum.\nPython 1.0 was released in 1994."
    )
    assert [claim.text for claim in claims] == [
        "Python was created by Guido van Rossum.",
        "Python 1.0 was released in 1994.",
    ]

