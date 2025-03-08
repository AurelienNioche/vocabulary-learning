"""Core vocabulary functions for formatting and validation."""

from typing import Dict, List, Tuple


def format_word_entry(
    word: str,
    translations: List[str],
    example_sentences: List[Tuple[str, str]],
) -> Dict:
    """Format a word entry for storage.

    Args:
        word: Japanese word
        translations: List of French translations
        example_sentences: List of (Japanese, French) example sentence pairs

    Returns
    -------
        Formatted word entry dictionary
    """
    return {
        "translations": translations,
        "example_sentences": [{"jp": jp, "fr": fr} for jp, fr in example_sentences],
    }


def validate_word_entry(entry: Dict) -> bool:
    """Validate a word entry's format.

    Args:
        entry: Word entry dictionary to validate

    Returns
    -------
        True if entry is valid
    """
    # Check required fields
    if not isinstance(entry, dict):
        return False
    if "translations" not in entry or "example_sentences" not in entry:
        return False

    # Validate translations
    if not isinstance(entry["translations"], list):
        return False
    if not entry["translations"]:  # Check if translations list is empty
        return False
    if not all(isinstance(t, str) and t.strip() for t in entry["translations"]):
        return False

    # Validate example sentences
    if not isinstance(entry["example_sentences"], list):
        return False
    for sentence in entry["example_sentences"]:
        if not isinstance(sentence, dict):
            return False
        if "jp" not in sentence or "fr" not in sentence:
            return False
        if not isinstance(sentence["jp"], str) or not isinstance(sentence["fr"], str):
            return False
        if not sentence["jp"].strip() or not sentence["fr"].strip():
            return False

    return True
