"""Unit tests for vocabulary core functions."""

import unittest

from rich.console import Console

from vocabulary_learning.core.vocabulary import format_word_entry, validate_word_entry


class TestVocabulary(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.console = Console(force_terminal=True)

    def test_format_word_entry_basic(self):
        """Test basic word entry formatting."""
        word = "こんにちは"
        translations = ["bonjour", "salut"]
        example_sentences = [
            ("こんにちは、元気ですか？", "Bonjour, comment allez-vous ?")
        ]

        result = format_word_entry(word, translations, example_sentences)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["translations"], translations)
        self.assertEqual(len(result["example_sentences"]), 1)
        self.assertEqual(
            result["example_sentences"][0]["jp"], "こんにちは、元気ですか？"
        )
        self.assertEqual(
            result["example_sentences"][0]["fr"], "Bonjour, comment allez-vous ?"
        )

    def test_format_word_entry_multiple_examples(self):
        """Test word entry formatting with multiple example sentences."""
        word = "新しい"
        translations = ["nouveau", "neuf"]
        example_sentences = [
            ("新しい車を買いました。", "J'ai acheté une nouvelle voiture."),
            ("これは新しいですか？", "Est-ce que c'est nouveau ?"),
        ]

        result = format_word_entry(word, translations, example_sentences)

        self.assertEqual(len(result["example_sentences"]), 2)
        self.assertEqual(result["example_sentences"][0]["jp"], "新しい車を買いました。")
        self.assertEqual(
            result["example_sentences"][0]["fr"], "J'ai acheté une nouvelle voiture."
        )
        self.assertEqual(result["example_sentences"][1]["jp"], "これは新しいですか？")
        self.assertEqual(
            result["example_sentences"][1]["fr"], "Est-ce que c'est nouveau ?"
        )

    def test_format_word_entry_empty_examples(self):
        """Test word entry formatting with no example sentences."""
        word = "はい"
        translations = ["oui"]
        example_sentences = []

        result = format_word_entry(word, translations, example_sentences)

        self.assertEqual(result["translations"], translations)
        self.assertEqual(result["example_sentences"], [])

    def test_validate_word_entry_valid(self):
        """Test validation of a valid word entry."""
        entry = {
            "translations": ["bonjour", "salut"],
            "example_sentences": [
                {
                    "jp": "こんにちは、元気ですか？",
                    "fr": "Bonjour, comment allez-vous ?",
                }
            ],
        }

        self.assertTrue(validate_word_entry(entry))

    def test_validate_word_entry_invalid_type(self):
        """Test validation with invalid entry type."""
        entry = ["not", "a", "dictionary"]
        self.assertFalse(validate_word_entry(entry))

    def test_validate_word_entry_missing_fields(self):
        """Test validation with missing required fields."""
        # Missing translations
        entry1 = {
            "example_sentences": [
                {
                    "jp": "こんにちは、元気ですか？",
                    "fr": "Bonjour, comment allez-vous ?",
                }
            ]
        }
        self.assertFalse(validate_word_entry(entry1))

        # Missing example_sentences
        entry2 = {"translations": ["bonjour", "salut"]}
        self.assertFalse(validate_word_entry(entry2))

    def test_validate_word_entry_invalid_translations(self):
        """Test validation with invalid translations."""
        # Empty translations list
        entry1 = {
            "translations": [],
            "example_sentences": [
                {
                    "jp": "こんにちは、元気ですか？",
                    "fr": "Bonjour, comment allez-vous ?",
                }
            ],
        }
        self.assertFalse(validate_word_entry(entry1))

        # Non-string translations
        entry2 = {
            "translations": [123, "bonjour"],
            "example_sentences": [
                {
                    "jp": "こんにちは、元気ですか？",
                    "fr": "Bonjour, comment allez-vous ?",
                }
            ],
        }
        self.assertFalse(validate_word_entry(entry2))

        # Empty string translations
        entry3 = {
            "translations": ["bonjour", ""],
            "example_sentences": [
                {
                    "jp": "こんにちは、元気ですか？",
                    "fr": "Bonjour, comment allez-vous ?",
                }
            ],
        }
        self.assertFalse(validate_word_entry(entry3))

    def test_validate_word_entry_invalid_example_sentences(self):
        """Test validation with invalid example sentences."""
        # Invalid example sentence type
        entry1 = {
            "translations": ["bonjour"],
            "example_sentences": "not a list",
        }
        self.assertFalse(validate_word_entry(entry1))

        # Invalid sentence structure
        entry2 = {
            "translations": ["bonjour"],
            "example_sentences": [["not", "a", "dict"]],
        }
        self.assertFalse(validate_word_entry(entry2))

        # Missing sentence fields
        entry3 = {
            "translations": ["bonjour"],
            "example_sentences": [{"jp": "こんにちは"}],  # Missing 'fr' field
        }
        self.assertFalse(validate_word_entry(entry3))

        # Invalid sentence field types
        entry4 = {
            "translations": ["bonjour"],
            "example_sentences": [{"jp": 123, "fr": "Bonjour"}],
        }
        self.assertFalse(validate_word_entry(entry4))

        # Empty sentence fields
        entry5 = {
            "translations": ["bonjour"],
            "example_sentences": [{"jp": "", "fr": "Bonjour"}],
        }
        self.assertFalse(validate_word_entry(entry5))


if __name__ == "__main__":
    unittest.main()
