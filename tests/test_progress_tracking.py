"""Unit tests for progress tracking functionality."""

import unittest
from datetime import datetime, timedelta

from vocabulary_learning.core.progress_tracking import (
    calculate_priority,
    count_active_learning_words,
    update_progress,
)


class TestProgressTracking(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.progress = {}
        self.save_called = False

        def mock_save_callback():
            self.save_called = True

        self.save_callback = mock_save_callback

    def test_new_word_initialization(self):
        """Test initializing progress for a new word."""
        update_progress("word_000001", False, self.progress, self.save_callback)

        self.assertIn("word_000001", self.progress)
        word_data = self.progress["word_000001"]
        self.assertEqual(word_data["attempts"], 1)
        self.assertEqual(word_data["successes"], 0)
        self.assertEqual(word_data["interval"], 0.0333)  # Failed attempt sets to minimum 2 minutes
        self.assertTrue(word_data["last_attempt_was_failure"])
        self.assertTrue(self.save_called)

    def test_interval_progression(self):
        """Test interval progression for successful attempts."""
        word_id = "word_000002"

        # First attempt (success)
        update_progress(word_id, True, self.progress, self.save_callback)
        self.assertEqual(self.progress[word_id]["interval"], 0.0333)  # First success: 2 minutes

        # Second attempt (success)
        update_progress(word_id, True, self.progress, self.save_callback)
        self.assertEqual(self.progress[word_id]["interval"], 24)  # Second success: 1 day

        # Third attempt (success) - should use easiness factor
        initial_interval = self.progress[word_id]["interval"]
        easiness = self.progress[word_id]["easiness_factor"]
        update_progress(word_id, True, self.progress, self.save_callback)
        self.assertEqual(self.progress[word_id]["interval"], initial_interval * easiness)

    def test_failed_attempt(self):
        """Test interval reduction on failed attempt."""
        word_id = "word_000003"

        # First success to set initial interval
        update_progress(word_id, True, self.progress, self.save_callback)
        initial_interval = self.progress[word_id]["interval"]

        # Failed attempt
        update_progress(word_id, False, self.progress, self.save_callback)
        self.assertEqual(self.progress[word_id]["interval"], max(0.0333, initial_interval * 0.5))
        self.assertTrue(self.progress[word_id]["last_attempt_was_failure"])

    def test_calculate_priority_new_word(self):
        """Test priority calculation for new words."""
        # Test with space for new words
        priority = calculate_priority(None, active_words_count=5)
        self.assertEqual(priority, 1.0)

        # Test when at max active words
        priority = calculate_priority(None, active_words_count=8)
        self.assertEqual(priority, 0.0)

    def test_calculate_priority_existing_word(self):
        """Test priority calculation for existing words."""
        # Create a word that's due for review
        word_data = {
            "successes": 4,
            "attempts": 5,
            "interval": 4,
            "last_seen": (datetime.now() - timedelta(hours=8)).isoformat(),
            "last_attempt_was_failure": True,
        }

        priority = calculate_priority(word_data, active_words_count=5)

        # Priority should be non-zero (word is overdue)
        self.assertGreater(priority, 0)
        # Priority should include failure bonus
        self.assertGreaterEqual(priority, 0.3)

    def test_count_active_learning_words(self):
        """Test counting active learning words."""
        progress = {
            "word_000001": {"attempts": 10, "successes": 9},  # 90% - mastered
            "word_000002": {"attempts": 10, "successes": 7},  # 70% - active
            "word_000003": {"attempts": 5, "successes": 2},  # 40% - active
            "word_000004": {"attempts": 0, "successes": 0},  # new word - not active
        }

        active_count = count_active_learning_words(progress)
        self.assertEqual(active_count, 2)

    def test_review_intervals_tracking(self):
        """Test tracking of review intervals."""
        word_id = "word_000004"

        # First attempt
        update_progress(word_id, True, self.progress, self.save_callback)
        self.assertEqual(len(self.progress[word_id]["review_intervals"]), 1)

        # Simulate time passing
        self.progress[word_id]["last_seen"] = (datetime.now() - timedelta(hours=2)).isoformat()

        # Second attempt
        update_progress(word_id, True, self.progress, self.save_callback)
        self.assertEqual(len(self.progress[word_id]["review_intervals"]), 2)
        self.assertAlmostEqual(self.progress[word_id]["review_intervals"][-1], 2, delta=0.1)

    def test_easiness_factor_adjustment(self):
        """Test adjustment of easiness factor."""
        word_id = "word_000005"

        # Initial easiness factor
        update_progress(word_id, True, self.progress, self.save_callback)
        initial_ef = self.progress[word_id]["easiness_factor"]

        # Success increases EF
        update_progress(word_id, True, self.progress, self.save_callback)
        self.assertGreater(self.progress[word_id]["easiness_factor"], initial_ef)

        # Failure decreases EF
        ef_before_failure = self.progress[word_id]["easiness_factor"]
        update_progress(word_id, False, self.progress, self.save_callback)
        self.assertLess(self.progress[word_id]["easiness_factor"], ef_before_failure)

        # EF should not go below 1.3
        for _ in range(5):  # Multiple failures
            update_progress(word_id, False, self.progress, self.save_callback)
        self.assertGreaterEqual(self.progress[word_id]["easiness_factor"], 1.3)


if __name__ == "__main__":
    unittest.main()
