"""Unit tests for vocabulary management functionality."""

import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
from rich.console import Console

from vocabulary_learning.core.vocabulary_management import add_vocabulary, reset_progress


class TestVocabularyManagement(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.console = Console()
        self.temp_dir = tempfile.mkdtemp()
        self.vocab_file = os.path.join(self.temp_dir, "vocabulary.json")
        self.progress_file = os.path.join(self.temp_dir, "progress.json")

        # Sample vocabulary DataFrame
        self.vocabulary = pd.DataFrame(
            [
                {
                    "japanese": "こんにちは",
                    "kanji": "今日は",
                    "french": "bonjour",
                    "example_sentence": "こんにちは、元気ですか？",
                }
            ]
        )

        # Sample progress data
        self.progress = {
            "こんにちは": {
                "attempts": 5,
                "successes": 4,
                "last_seen": datetime.now().isoformat(),
            }
        }

        # Mock Firebase reference
        self.mock_ref = MagicMock()

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.vocab_file):
            os.remove(self.vocab_file)
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        # Clean up backup files
        for f in os.listdir(self.temp_dir):
            if f.startswith("progress.json.backup"):
                os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    @patch("builtins.input")
    def test_add_vocabulary_success(self, mock_input):
        """Test adding new vocabulary successfully."""
        # Mock user inputs
        mock_input.side_effect = [
            "あたらしい",  # Japanese
            "新しい",  # Kanji
            "nouveau",  # French
            "新しい車を買いました。",  # Example
            "n",  # Don't add another word
        ]

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(
                self.vocab_file,
                self.vocabulary,
                self.mock_ref,
                self.console,
                mock_load_vocab,
            )

        # Verify file was created
        self.assertTrue(os.path.exists(self.vocab_file))

        # Check file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify word was added
        self.assertEqual(len(vocab_data), 1)
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "あたらしい")
        self.assertEqual(vocab_data[word_id]["kanji"], "新しい")
        self.assertEqual(vocab_data[word_id]["french"], "nouveau")
        self.assertEqual(vocab_data[word_id]["example_sentence"], "新しい車を買いました。")

        # Verify Firebase sync
        self.mock_ref.set.assert_called_once_with(vocab_data)

    @patch("builtins.input")
    @patch("rich.prompt.Confirm.ask", return_value=False)
    def test_add_vocabulary_duplicate(self, mock_confirm, mock_input):
        """Test adding duplicate vocabulary."""
        # Create existing vocabulary file
        with open(self.vocab_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "word_000001": {
                        "hiragana": "あたらしい",
                        "kanji": "新しい",
                        "french": "nouveau",
                        "example_sentence": "",
                    }
                },
                f,
            )

        # Mock user inputs - provide enough inputs for both the duplicate case and a new word
        mock_input.side_effect = [
            "あたらしい",  # Japanese (duplicate)
            "q",  # Quit after duplicate is detected
        ]

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        # Create DataFrame with existing word
        vocabulary = pd.DataFrame([{"japanese": "あたらしい"}])

        add_vocabulary(self.vocab_file, vocabulary, None, self.console, mock_load_vocab)

        # Verify file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify word was not added again
        self.assertEqual(len(vocab_data), 1)
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "あたらしい")

    @patch("builtins.input")
    def test_add_vocabulary_missing_required_fields(self, mock_input):
        """Test adding vocabulary with missing required fields."""
        # Mock user inputs
        mock_input.side_effect = [
            "あたらしい",  # Japanese
            "",  # Kanji (empty)
            "",  # French (empty)
            "",  # Example (empty)
            "n",  # Don't add another word
        ]

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        add_vocabulary(self.vocab_file, self.vocabulary, None, self.console, mock_load_vocab)

        # Verify file was created
        self.assertTrue(os.path.exists(self.vocab_file))

        # Check file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify word was added
        self.assertEqual(len(vocab_data), 1)
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "あたらしい")
        self.assertEqual(vocab_data[word_id]["kanji"], "")

    @patch("builtins.input")
    def test_add_vocabulary_firebase_sync_failure(self, mock_input):
        """Test adding vocabulary with Firebase sync failure."""
        # Mock user inputs
        mock_input.side_effect = [
            "あたらしい",  # Japanese
            "新しい",  # Kanji
            "nouveau",  # French
            "",  # Example (empty)
            "n",  # Don't add another word
        ]

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        # Make Firebase sync fail
        mock_ref = MagicMock()
        mock_ref.set.side_effect = Exception("Firebase sync failed")

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(
                self.vocab_file, self.vocabulary, mock_ref, self.console, mock_load_vocab
            )

        # Verify file was still created locally
        self.assertTrue(os.path.exists(self.vocab_file))

    @patch("rich.prompt.Confirm.ask")
    def test_reset_progress_confirmed(self, mock_confirm):
        """Test resetting progress with confirmation."""
        # Create progress file
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f)

        # Mock confirmation
        mock_confirm.return_value = True

        # Mock save callback
        mock_save = MagicMock()

        reset_progress(self.progress_file, self.mock_ref, self.progress, mock_save, self.console)

        # Verify progress was cleared
        self.assertEqual(len(self.progress), 0)
        mock_save.assert_called_once()

        # Verify backup was created
        backup_files = [
            f for f in os.listdir(self.temp_dir) if f.startswith("progress.json.backup")
        ]
        self.assertEqual(len(backup_files), 1)

        # Verify Firebase was reset
        self.mock_ref.set.assert_called_once_with({})

    @patch("rich.prompt.Confirm.ask")
    def test_reset_progress_cancelled(self, mock_confirm):
        """Test cancelling progress reset."""
        # Create progress file
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f)

        # Mock confirmation
        mock_confirm.return_value = False

        # Mock save callback
        mock_save = MagicMock()

        reset_progress(self.progress_file, self.mock_ref, self.progress, mock_save, self.console)

        # Verify progress was not cleared
        self.assertEqual(len(self.progress), 1)
        mock_save.assert_not_called()

        # Verify no backup was created
        backup_files = [
            f for f in os.listdir(self.temp_dir) if f.startswith("progress.json.backup")
        ]
        self.assertEqual(len(backup_files), 0)

        # Verify Firebase was not reset
        self.mock_ref.set.assert_not_called()

    @patch("rich.prompt.Confirm.ask")
    def test_reset_progress_firebase_failure(self, mock_confirm):
        """Test resetting progress with Firebase failure."""
        # Create progress file
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f)

        # Mock confirmation
        mock_confirm.return_value = True

        # Mock save callback
        mock_save = MagicMock()

        # Make Firebase reset fail
        mock_ref = MagicMock()
        mock_ref.set.side_effect = Exception("Firebase reset failed")

        reset_progress(self.progress_file, mock_ref, self.progress, mock_save, self.console)

        # Verify progress was still cleared locally
        self.assertEqual(len(self.progress), 0)
        mock_save.assert_called_once()

        # Verify backup was created
        backup_files = [
            f for f in os.listdir(self.temp_dir) if f.startswith("progress.json.backup")
        ]
        self.assertEqual(len(backup_files), 1)

    @patch("builtins.input")
    def test_add_vocabulary_with_old_format(self, mock_input):
        """Test adding vocabulary when existing file uses old list format."""
        # Create existing vocabulary file with old list format
        with open(self.vocab_file, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "japanese": "こんにちは",
                        "kanji": "今日は",
                        "french": "bonjour",
                        "example_sentence": "",
                    }
                ],
                f,
            )

        # Mock user inputs
        mock_input.side_effect = [
            "さっき",  # Japanese
            "",  # Kanji (empty)
            "à l'instant",  # French
            "",  # Example (empty)
            "n",  # Don't add another word
        ]

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(self.vocab_file, self.vocabulary, None, self.console, mock_load_vocab)

        # Verify file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify both words are present in dictionary format
        self.assertEqual(len(vocab_data), 2)
        self.assertTrue(isinstance(vocab_data, dict))
        self.assertTrue(any(word["hiragana"] == "こんにちは" for word in vocab_data.values()))
        self.assertTrue(any(word["hiragana"] == "さっき" for word in vocab_data.values()))

    @patch("builtins.input")
    def test_add_vocabulary_with_invalid_format(self, mock_input):
        """Test adding vocabulary when existing file has invalid format."""
        # Create existing vocabulary file with invalid format (not a dict)
        with open(self.vocab_file, "w", encoding="utf-8") as f:
            json.dump(["some", "invalid", "data"], f)

        # Mock user inputs
        mock_input.side_effect = [
            "さっき",  # Japanese
            "",  # Kanji (empty)
            "à l'instant",  # French
            "",  # Example (empty)
            "n",  # Don't add another word
        ]

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(self.vocab_file, self.vocabulary, None, self.console, mock_load_vocab)

        # Verify file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify the word was added to a fresh dictionary
        self.assertEqual(len(vocab_data), 1)
        self.assertTrue(isinstance(vocab_data, dict))
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "さっき")
        self.assertEqual(vocab_data[word_id]["french"], "à l'instant")


if __name__ == "__main__":
    unittest.main()
