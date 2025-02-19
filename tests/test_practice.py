"""Unit tests for practice mode functionality."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
from rich.console import Console

from vocabulary_learning.core.practice import check_answer, practice_mode, select_word


class TestPractice(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.console = Console(force_terminal=True)
        self.mock_converter = MagicMock()
        self.mock_converter.kks.convert.return_value = [{"hira": "ひらがな"}]
        self.mock_update_progress = MagicMock()
        self.mock_show_help = MagicMock()
        self.mock_show_stats = MagicMock()
        self.mock_save_progress = MagicMock()

        # Create test vocabulary
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
            ]
        )

        # Create test progress data
        self.progress = {
            "000001": {
                "attempts": 5,
                "successes": 2,
                "last_seen": "2024-02-10T12:00:00",
                "review_intervals": [1, 4],
                "last_attempt_was_failure": False,
                "interval": 4,
                "easiness_factor": 2.5,
            },
            "000002": {
                "attempts": 3,
                "successes": 1,
                "last_seen": "2024-02-11T12:00:00",
                "review_intervals": [1],
                "last_attempt_was_failure": True,
                "interval": 1,
                "easiness_factor": 2.5,
            },
        }

    def test_select_word_new_word(self):
        """Test word selection prioritizing new words."""
        # Create a fresh progress with a word that's not due (future date)
        # and has a success rate below mastery
        progress = {
            "000001": {
                "attempts": 10,
                "successes": 9,  # 90% success rate to be considered mastered
                "last_seen": "2025-02-11T12:00:00",  # Future date to ensure it's not due
                "review_intervals": [1, 4, 24],
                "last_attempt_was_failure": False,
                "interval": 24,
                "easiness_factor": 2.5,
            }
        }
        # Since the word in progress is mastered, it should be skipped
        # and the new word should be selected
        selected = select_word(self.vocabulary, progress, self.console)
        self.assertNotEqual(selected["japanese"], "こんにちは")

    def test_select_word_active_limit(self):
        """Test word selection respecting active words limit."""
        # Add more active words to reach the limit
        progress = self.progress.copy()
        for i in range(8):
            progress[str(i + 1).zfill(6)] = {
                "attempts": 5,
                "successes": 2,
                "last_seen": "2024-02-11T12:00:00",
                "interval": 4,
                "last_attempt_was_failure": False,
                "review_intervals": [1, 4],
                "easiness_factor": 2.5,
            }

        selected = select_word(self.vocabulary, progress, self.console)
        self.assertIsNotNone(selected)

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

    def test_new_words_suggested_after_mastery(self):
        """Test that new words are suggested when words are mastered."""
        # Create a progress dictionary with 8 mastered words
        progress = {}
        for i in range(8):
            progress[str(i + 1).zfill(6)] = {
                "attempts": 10,
                "successes": 9,  # 90% success rate
                "last_seen": "2024-02-11T12:00:00",
                "interval": 24,
                "last_attempt_was_failure": False,
                "review_intervals": [1, 4, 24],
                "easiness_factor": 2.5,
            }

        # Create a vocabulary with the mastered words plus some new ones
        vocab_data = []
        # Add the mastered words
        for i in range(8):
            vocab_data.append(
                {
                    "japanese": f"word_{i}",
                    "kanji": "",
                    "french": f"french_{i}",
                    "example_sentence": "",
                }
            )
        # Add some new words
        for i in range(8, 12):
            vocab_data.append(
                {
                    "japanese": f"word_{i}",
                    "kanji": "",
                    "french": f"french_{i}",
                    "example_sentence": "",
                }
            )
        vocabulary = pd.DataFrame(vocab_data)

        # Test word selection
        selected = select_word(vocabulary, progress, self.console)
        self.assertIn(selected["japanese"], [f"word_{i}" for i in range(8, 12)])

    def test_word_mastery_criteria(self):
        """Test the criteria for considering a word mastered."""
        from vocabulary_learning.core.progress_tracking import count_active_learning_words

        progress = {
            # Word with high success rate but not enough attempts
            "word_1": {
                "attempts": 4,
                "successes": 4,  # 100% but only 4 successes
                "last_seen": "2024-02-11T12:00:00",
                "interval": 0.0333,  # 2 minutes
            },
            # Word with enough attempts but low success rate
            "word_2": {
                "attempts": 10,
                "successes": 8,  # 80% success rate
                "last_seen": "2024-02-11T12:00:00",
                "interval": 24,  # 1 day
            },
            # Word that meets mastery criteria
            "word_3": {
                "attempts": 10,
                "successes": 9,  # 90% success rate
                "last_seen": "2024-02-11T12:00:00",
                "interval": 48,  # 2 days
            },
            # Word that exceeds mastery criteria
            "word_4": {
                "attempts": 15,
                "successes": 14,  # 93% success rate
                "last_seen": "2024-02-11T12:00:00",
                "interval": 96,  # 4 days
            },
        }

        # Count active words (should be 2 - word_1 and word_2)
        active_count = count_active_learning_words(progress)
        self.assertEqual(active_count, 2, "Only non-mastered words should be counted as active")

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
    @patch("builtins.input", side_effect=["au revoir", ":q"])
    def test_practice_mode_correct_answer(self, mock_input, mock_exit):
        """Test practice mode with correct answer."""
        # Use a progress dictionary that won't prioritize failed words
        progress = {
            "000002": {
                "attempts": 5,
                "successes": 2,
                "last_seen": "2024-02-10T12:00:00",
                "review_intervals": [1, 4],
                "last_attempt_was_failure": False,
                "interval": 4,
                "easiness_factor": 2.5,
            }
        }
        with self.assertRaises(SystemExit):
            practice_mode(
                self.vocabulary,
                progress,
                self.console,
                self.mock_converter,
                self.mock_update_progress,
                self.mock_show_help,
                self.mock_show_stats,
                self.mock_save_progress,
            )

        # Verify update_progress was called with success=True
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
