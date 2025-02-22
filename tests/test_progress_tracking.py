"""Unit tests for progress tracking functionality."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import pytz

from vocabulary_learning.core.progress_tracking import (
    calculate_priority,
    calculate_weighted_success_rate,
    count_active_learning_words,
    get_utc_now,
    is_mastered,
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
        self.assertTrue(isinstance(word_data["attempt_history"], list))
        self.assertEqual(len(word_data["attempt_history"]), 1)
        self.assertTrue(self.save_called)

    def test_weighted_success_rate(self):
        """Test the weighted success rate calculation with temporal decay."""
        now = datetime.now(pytz.UTC)

        # Create attempt history with known timestamps
        attempt_history = [
            # Recent attempts (last day)
            {"timestamp": (now - timedelta(hours=1)).isoformat(), "success": True},
            {"timestamp": (now - timedelta(hours=2)).isoformat(), "success": True},
            # Older attempts (last week)
            {"timestamp": (now - timedelta(days=7)).isoformat(), "success": False},
            {"timestamp": (now - timedelta(days=8)).isoformat(), "success": True},
            # Very old attempts (last month)
            {"timestamp": (now - timedelta(days=30)).isoformat(), "success": True},
            {"timestamp": (now - timedelta(days=31)).isoformat(), "success": True},
        ]

        # Calculate weighted success rate
        rate = calculate_weighted_success_rate(attempt_history, now)

        # Recent failures should have more impact than old successes
        self.assertGreater(rate, 0.5)  # Should be high due to recent successes
        self.assertLess(rate, 1.0)  # But not perfect due to the week-old failure

    def test_mastery_criteria_with_decay(self):
        """Test mastery criteria with temporal decay."""
        now = datetime.now(pytz.UTC)

        # Case 1: Word with recent successes
        recent_success_history = [
            {"timestamp": (now - timedelta(hours=i)).isoformat(), "success": True}
            for i in range(1, 6)
        ]
        word_data = {"attempts": 5, "successes": 5, "attempt_history": recent_success_history}
        self.assertTrue(is_mastered(word_data))

        # Case 2: Word with old successes but recent failures
        mixed_history = [
            # Recent failures
            {"timestamp": (now - timedelta(hours=1)).isoformat(), "success": False},
            {"timestamp": (now - timedelta(hours=2)).isoformat(), "success": False},
            # Old successes
            *[
                {"timestamp": (now - timedelta(days=30 + i)).isoformat(), "success": True}
                for i in range(5)
            ],
        ]
        word_data = {"attempts": 7, "successes": 5, "attempt_history": mixed_history}
        self.assertFalse(is_mastered(word_data))

        # Case 3: Word with consistent success over time
        consistent_history = [
            *[
                {"timestamp": (now - timedelta(hours=i)).isoformat(), "success": True}
                for i in range(1, 3)
            ],
            *[
                {"timestamp": (now - timedelta(days=7 + i)).isoformat(), "success": True}
                for i in range(2)
            ],
            *[
                {"timestamp": (now - timedelta(days=30 + i)).isoformat(), "success": True}
                for i in range(2)
            ],
        ]
        word_data = {"attempts": 6, "successes": 6, "attempt_history": consistent_history}
        self.assertTrue(is_mastered(word_data))

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

        # Failed attempt
        update_progress(word_id, False, self.progress, self.save_callback)
        self.assertEqual(self.progress[word_id]["interval"], 0.0333)  # Reset to 2 minutes
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
        now = datetime.now(pytz.UTC)

        # Create progress data with various word states
        progress = {
            "word_000001": {  # Mastered word with recent successes
                "attempts": 10,
                "successes": 9,
                "attempt_history": [
                    {"timestamp": (now - timedelta(hours=i)).isoformat(), "success": True}
                    for i in range(1, 10)
                ],
            },
            "word_000002": {  # Active word with mixed recent performance (below 80% success rate)
                "attempts": 10,
                "successes": 7,
                "attempt_history": [
                    {"timestamp": (now - timedelta(hours=1)).isoformat(), "success": False},
                    {"timestamp": (now - timedelta(hours=2)).isoformat(), "success": False},
                    {"timestamp": (now - timedelta(hours=3)).isoformat(), "success": False},
                    *[
                        {"timestamp": (now - timedelta(days=i)).isoformat(), "success": True}
                        for i in range(1, 8)
                    ],
                ],
            },
            "word_000003": {  # New word with few attempts
                "attempts": 3,
                "successes": 2,
                "attempt_history": [
                    {"timestamp": (now - timedelta(hours=i)).isoformat(), "success": i != 1}
                    for i in range(1, 4)
                ],
            },
            "word_000004": {  # Word with no attempts
                "attempts": 0,
                "successes": 0,
                "attempt_history": [],
            },
        }

        active_count = count_active_learning_words(progress)
        self.assertEqual(
            active_count,
            2,  # word_000002 and word_000003
            "Only non-mastered words with attempts should be counted as active",
        )

    @patch("vocabulary_learning.core.progress_tracking.get_utc_now")
    def test_review_intervals_tracking(self, mock_get_utc_now):
        """Test tracking of review intervals."""
        word_id = "word_000004"

        # Mock current time
        now = datetime.now(pytz.UTC)
        mock_get_utc_now.return_value = now

        # First attempt
        update_progress(word_id, True, self.progress, self.save_callback)
        self.assertEqual(len(self.progress[word_id]["review_intervals"]), 1)

        # Simulate time passing (2 hours)
        two_hours_later = now + timedelta(hours=2)
        mock_get_utc_now.return_value = two_hours_later

        # Second attempt
        update_progress(word_id, True, self.progress, self.save_callback)
        self.assertEqual(len(self.progress[word_id]["review_intervals"]), 2)
        self.assertAlmostEqual(self.progress[word_id]["review_intervals"][-1], 2, delta=0.1)

    def test_easiness_factor_adjustment(self):
        """Test adjustment of easiness factor."""
        word_id = "word_000005"

        # Initialize with a lower easiness factor
        self.progress[word_id] = {
            "attempts": 0,
            "successes": 0,
            "interval": 0,
            "last_attempt_was_failure": False,
            "last_seen": datetime.now().isoformat(),
            "review_intervals": [],
            "easiness_factor": 2.0,  # Start with a lower value
        }

        # Success increases EF
        update_progress(word_id, True, self.progress, self.save_callback)
        self.assertGreater(self.progress[word_id]["easiness_factor"], 2.0)

        # Failure decreases EF
        update_progress(word_id, False, self.progress, self.save_callback)
        self.assertLess(self.progress[word_id]["easiness_factor"], 2.1)


if __name__ == "__main__":
    unittest.main()
