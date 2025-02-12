"""Unit tests for practice mode functionality."""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from rich.console import Console

from vocabulary_learning.core.practice import check_answer, practice_mode, select_word


class TestPractice(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.console = Console()

        # Sample vocabulary data
        self.vocabulary = pd.DataFrame(
            [
                {
                    "japanese": "こんにちは",
                    "kanji": "今日は",
                    "french": "bonjour",
                    "example_sentence": "こんにちは、元気ですか？",
                },
                {
                    "japanese": "さようなら",
                    "kanji": "",
                    "french": "au revoir",
                    "example_sentence": "",
                },
                {
                    "japanese": "新しい",
                    "kanji": "新しい",
                    "french": "nouveau/neuf",
                    "example_sentence": "新しい車を買いました。",
                },
            ]
        )

        # Sample progress data
        self.progress = {
            "こんにちは": {
                "attempts": 10,
                "successes": 8,
                "last_seen": "2024-02-11T12:00:00",
                "review_intervals": [1, 4, 24],
                "last_attempt_was_failure": False,
                "interval": 24,
            },
            "さようなら": {
                "attempts": 5,
                "successes": 2,
                "last_seen": "2024-02-10T12:00:00",
                "review_intervals": [1, 4],
                "last_attempt_was_failure": True,
                "interval": 4,
            },
        }

        # Mock functions
        self.mock_update_progress = MagicMock()
        self.mock_show_help = MagicMock()
        self.mock_show_stats = MagicMock()
        self.mock_save_progress = MagicMock()
        self.mock_converter = MagicMock()

    def test_select_word_new_word(self):
        """Test word selection prioritizing new words."""
        selected = select_word(self.vocabulary, self.progress)
        self.assertEqual(selected["japanese"], "新しい")  # Should select the unlearned word

    def test_select_word_active_limit(self):
        """Test word selection respecting active words limit."""
        # Add more active words to reach the limit
        progress = self.progress.copy()
        for i in range(8):
            progress[f"word_{i}"] = {
                "attempts": 5,
                "successes": 2,
                "last_seen": "2024-02-11T12:00:00",
                "interval": 4,
            }

        selected = select_word(self.vocabulary, progress)
        self.assertIsNotNone(selected)  # Should still select a word
        self.assertNotEqual(selected["japanese"], "新しい")  # Should not select new word

    def test_check_answer_exact_match(self):
        """Test answer checking with exact match."""
        is_correct, message = check_answer("bonjour", "bonjour")
        self.assertTrue(is_correct)
        self.assertIsNone(message)

    def test_check_answer_multiple_answers(self):
        """Test answer checking with multiple correct answers."""
        is_correct, message = check_answer("nouveau", "nouveau/neuf")
        self.assertTrue(is_correct)
        self.assertIn("would be correct", message)

    def test_check_answer_case_insensitive(self):
        """Test case-insensitive answer checking."""
        is_correct, message = check_answer("Bonjour", "bonjour")
        self.assertTrue(is_correct)
        self.assertIsNone(message)

    def test_check_answer_with_typo(self):
        """Test answer checking with minor typo."""
        with patch("vocabulary_learning.core.practice.Confirm.ask", return_value=True):
            is_correct, message = check_answer("binjour", "bonjour")
            self.assertTrue(is_correct)
            self.assertIn("correct spelling", message)

    def test_check_answer_incorrect(self):
        """Test answer checking with incorrect answer."""
        is_correct, message = check_answer("hello", "bonjour")
        self.assertFalse(is_correct)
        self.assertIsNone(message)

    @patch("vocabulary_learning.core.practice.exit_with_save", side_effect=SystemExit)
    @patch("builtins.input", side_effect=[":h", ":s", ":q"])
    def test_practice_mode_commands(self, mock_input, mock_exit):
        """Test practice mode command handling."""
        with self.assertRaises(SystemExit):
            practice_mode(
                self.vocabulary,
                self.progress,
                self.console,
                self.mock_converter,
                self.mock_update_progress,
                self.mock_show_help,
                self.mock_show_stats,
                self.mock_save_progress,
            )

        # Verify command handlers were called
        self.mock_show_help.assert_called_once()
        self.mock_show_stats.assert_called_once()
        mock_exit.assert_called_once()

    @patch("vocabulary_learning.core.practice.exit_with_save", side_effect=SystemExit)
    @patch("builtins.input", side_effect=["nouveau", ":q"])
    def test_practice_mode_correct_answer(self, mock_input, mock_exit):
        """Test practice mode with correct answer."""
        with self.assertRaises(SystemExit):
            practice_mode(
                self.vocabulary,
                self.progress,
                self.console,
                self.mock_converter,
                self.mock_update_progress,
                self.mock_show_help,
                self.mock_show_stats,
                self.mock_save_progress,
            )

        # Verify progress was updated
        self.mock_update_progress.assert_called_once()
        args = self.mock_update_progress.call_args[0]
        self.assertEqual(args[1], True)  # Second argument should be success=True
        mock_exit.assert_called_once()

    @patch("vocabulary_learning.core.practice.exit_with_save", side_effect=SystemExit)
    @patch("builtins.input", side_effect=["wrong", "bonjour", ":q"])
    def test_practice_mode_incorrect_answer(self, mock_input, mock_exit):
        """Test practice mode with incorrect answer."""
        with self.assertRaises(SystemExit):
            practice_mode(
                self.vocabulary,
                self.progress,
                self.console,
                self.mock_converter,
                self.mock_update_progress,
                self.mock_show_help,
                self.mock_show_stats,
                self.mock_save_progress,
            )

        # Verify progress was updated for the failure
        self.mock_update_progress.assert_called()
        first_call_args = self.mock_update_progress.call_args_list[0][0]
        self.assertEqual(first_call_args[1], False)  # Second argument should be success=False
        mock_exit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
