"""Unit tests for UI components."""

import unittest
from datetime import datetime, timedelta

import pandas as pd
from rich.console import Console

from vocabulary_learning.core.constants import VIM_COMMANDS
from vocabulary_learning.core.ui_components import (
    show_help,
    show_progress,
    show_save_status,
    show_word_statistics,
)


class TestUIComponents(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.console = Console(force_terminal=True)

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
            ]
        )

        # Sample progress data
        self.progress = {
            "word_000001": {
                "attempts": 10,
                "successes": 8,  # 80% success rate
                "interval": 24,
                "last_attempt_was_failure": False,
                "last_seen": datetime.now().isoformat(),
                "review_intervals": [1, 4, 24],
                "easiness_factor": 2.5,
            },
            "word_000002": {
                "attempts": 5,
                "successes": 2,  # 40% success rate
                "interval": 4,
                "last_attempt_was_failure": True,
                "last_seen": datetime.now().isoformat(),
                "review_intervals": [1, 4],
                "easiness_factor": 2.3,
            },
        }

        # Sample vim commands
        self.vim_commands = VIM_COMMANDS

    def test_show_progress(self):
        """Test progress display."""
        # Capture the output
        with self.console.capture() as capture:
            show_progress(self.vocabulary, self.progress, self.console)

        output = capture.get()

        # Check if key information is present (accounting for truncated text)
        self.assertIn("こんにち", output)  # Checking truncated text
        self.assertIn("今日は", output)
        self.assertIn("bonjour", output)
        self.assertIn("80%", output)  # Success rate for first word
        self.assertIn("40%", output)  # Success rate for second word

    def test_show_word_statistics(self):
        """Test word statistics display."""
        word_pair = self.vocabulary.iloc[0]

        with self.console.capture() as capture:
            show_word_statistics(word_pair, self.progress, self.console)

        output = capture.get()

        # Check if statistics are present
        self.assertIn("こんにちは", output)
        self.assertIn("80%", output)  # Success rate
        self.assertIn("10", output)  # Total attempts
        self.assertIn("8", output)  # Successful attempts
        self.assertIn("2", output)  # Failed attempts

    def test_show_save_status(self):
        """Test save status display."""
        progress_file = "test_progress.json"
        last_save_time = datetime.now() - timedelta(seconds=30)

        with self.console.capture() as capture:
            show_save_status(progress_file, self.progress, last_save_time, self.console)

        output = capture.get()

        # Check if save information is present
        self.assertIn("Auto-save Status", output)
        self.assertIn("test_progress.json", output)  # File name
        self.assertIn("Words Tracked", output)  # Check for header instead of specific count

    def test_show_help(self):
        """Test help display."""
        with self.console.capture() as capture:
            show_help(self.vim_commands, self.console)

        output = capture.get()

        # Check if all commands are shown
        for cmd, desc in self.vim_commands.items():
            self.assertIn(cmd, output)
            self.assertIn(desc, output)

    def test_progress_display_with_empty_data(self):
        """Test progress display with empty data."""
        empty_vocab = pd.DataFrame(columns=["japanese", "kanji", "french"])
        empty_progress = {}

        with self.console.capture() as capture:
            show_progress(empty_vocab, empty_progress, self.console)

        output = capture.get()
        self.assertTrue(len(output.strip()) > 0)  # Should still show table headers

    def test_word_statistics_with_missing_progress(self):
        """Test word statistics for word without progress data."""
        word_pair = pd.Series({"japanese": "新しい", "kanji": "新しい", "french": "nouveau"})

        with self.console.capture() as capture:
            show_word_statistics(word_pair, self.progress, self.console)

        output = capture.get()
        self.assertIn("新しい", output)
        self.assertIn("0%", output)  # Should show 0% success rate

    def test_save_status_with_nonexistent_file(self):
        """Test save status display with nonexistent file."""
        with self.console.capture() as capture:
            show_save_status("nonexistent.json", {}, datetime.now(), self.console)

        output = capture.get()
        self.assertIn("No save file found", output)


if __name__ == "__main__":
    unittest.main()
