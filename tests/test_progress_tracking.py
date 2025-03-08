"""Unit tests for progress tracking functionality."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import pytz

from vocabulary_learning.core.progress_tracking import (
    MAX_ACTIVE_WORDS,
    calculate_priority,
    calculate_weighted_success_rate,
    count_active_learning_words,
    is_mastered,
    is_newly_introduced,
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
        self.assertEqual(
            word_data["interval"], 0.0333
        )  # Failed attempt sets to minimum 2 minutes
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

    def test_attempt_history_tracking(self):
        """Test that attempt history is properly tracked in progress updates."""
        progress = {}
        save_called = False

        def mock_save_callback():
            nonlocal save_called
            save_called = True

        # First attempt (success)
        word_id = "word_000001"
        update_progress(word_id, True, progress, mock_save_callback)

        # Verify attempt history was initialized and updated
        self.assertIn("attempt_history", progress[word_id])
        self.assertEqual(len(progress[word_id]["attempt_history"]), 1)
        self.assertTrue(progress[word_id]["attempt_history"][0]["success"])

        # Second attempt (failure)
        update_progress(word_id, False, progress, mock_save_callback)

        # Verify attempt history was updated
        self.assertEqual(len(progress[word_id]["attempt_history"]), 2)
        self.assertFalse(progress[word_id]["attempt_history"][1]["success"])

        # Verify basic stats are correct
        self.assertEqual(progress[word_id]["attempts"], 2)
        self.assertEqual(progress[word_id]["successes"], 1)

        # Calculate weighted success rate
        rate = calculate_weighted_success_rate(progress[word_id]["attempt_history"])

        # Recent failure should weigh more than older success
        self.assertLess(rate, 0.5)

    def test_mastery_criteria_with_decay(self):
        """Test mastery criteria with temporal decay."""
        now = datetime.now(pytz.UTC)

        # Case 1: Word with recent successes
        recent_success_history = [
            {"timestamp": (now - timedelta(hours=i)).isoformat(), "success": True}
            for i in range(1, 6)
        ]
        word_data = {
            "attempts": 5,
            "successes": 5,
            "attempt_history": recent_success_history,
        }
        self.assertTrue(is_mastered(word_data))

        # Case 2: Word with old successes but recent failures
        mixed_history = [
            # Recent failures
            {"timestamp": (now - timedelta(hours=1)).isoformat(), "success": False},
            {"timestamp": (now - timedelta(hours=2)).isoformat(), "success": False},
            # Old successes
            *[
                {
                    "timestamp": (now - timedelta(days=30 + i)).isoformat(),
                    "success": True,
                }
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
                {
                    "timestamp": (now - timedelta(days=7 + i)).isoformat(),
                    "success": True,
                }
                for i in range(2)
            ],
            *[
                {
                    "timestamp": (now - timedelta(days=30 + i)).isoformat(),
                    "success": True,
                }
                for i in range(2)
            ],
        ]
        word_data = {
            "attempts": 6,
            "successes": 6,
            "attempt_history": consistent_history,
        }
        self.assertTrue(is_mastered(word_data))

    def test_interval_progression(self):
        """Test interval progression for successful attempts."""
        word_id = "word_000002"

        # First attempt (success)
        update_progress(word_id, True, self.progress, self.save_callback)
        self.assertEqual(
            self.progress[word_id]["interval"], 0.0333
        )  # First success: 2 minutes

        # Second attempt (success)
        update_progress(word_id, True, self.progress, self.save_callback)
        self.assertEqual(
            self.progress[word_id]["interval"], 24
        )  # Second success: 1 day

        # Third attempt (success) - Now uses hours_since_last * easiness_factor
        # This test is no longer valid with our modified algorithm since we're using elapsed time
        # instead of the previous interval for progression
        # In the modified algorithm, the interval will be close to zero because the test
        # runs quickly and hours_since_last will be very small
        easiness = self.progress[word_id]["easiness_factor"]

        # Mock the elapsed time to test the new algorithm
        with patch(
            "vocabulary_learning.core.progress_tracking.get_utc_now"
        ) as mock_get_utc_now:
            # First get the current time
            current_time = datetime.now(pytz.UTC)
            # Set up the mock to return a time 10 hours later
            mock_get_utc_now.return_value = current_time + timedelta(hours=10)

            # Update progress with our mocked time
            update_progress(word_id, True, self.progress, self.save_callback)

            # With our mocked 10 hour elapsed time, and easiness factor of 2.5 (default)
            # we expect interval to be approximately 10 * 2.5 = 25 hours
            self.assertAlmostEqual(
                self.progress[word_id]["interval"], 10 * easiness, delta=0.1
            )

    def test_failed_attempt(self):
        """Test interval reduction on failed attempt."""
        word_id = "word_000003"

        # First success to set initial interval
        update_progress(word_id, True, self.progress, self.save_callback)

        # Failed attempt
        update_progress(word_id, False, self.progress, self.save_callback)
        self.assertEqual(
            self.progress[word_id]["interval"], 0.0333
        )  # Reset to 2 minutes
        self.assertTrue(self.progress[word_id]["last_attempt_was_failure"])

    def test_calculate_priority_new_word(self):
        """Test priority calculation for new words."""
        # Test with space for new words
        # New words get priority 0.8 to ensure overdue words (ratio > 1.0)
        # or failed words (bonus 0.3) take precedence
        priority = calculate_priority(None, active_words_count=5)
        self.assertEqual(priority, 0.8)

        # Test when at max active words
        priority = calculate_priority(None, active_words_count=MAX_ACTIVE_WORDS)
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
                    {
                        "timestamp": (now - timedelta(hours=i)).isoformat(),
                        "success": True,
                    }
                    for i in range(1, 10)
                ],
            },
            "word_000002": {  # Active word with mixed recent performance (below 80% success rate)
                "attempts": 10,
                "successes": 7,
                "attempt_history": [
                    {
                        "timestamp": (now - timedelta(hours=1)).isoformat(),
                        "success": False,
                    },
                    {
                        "timestamp": (now - timedelta(hours=2)).isoformat(),
                        "success": False,
                    },
                    {
                        "timestamp": (now - timedelta(hours=3)).isoformat(),
                        "success": False,
                    },
                    *[
                        {
                            "timestamp": (now - timedelta(days=i)).isoformat(),
                            "success": True,
                        }
                        for i in range(1, 8)
                    ],
                ],
            },
            "word_000003": {  # New word with few attempts
                "attempts": 3,
                "successes": 2,
                "attempt_history": [
                    {
                        "timestamp": (now - timedelta(hours=i)).isoformat(),
                        "success": i != 1,
                    }
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
        self.assertAlmostEqual(
            self.progress[word_id]["review_intervals"][-1], 2, delta=0.1
        )

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

    def test_easiness_factor_max_limit(self):
        """Test that easiness factor is properly adjusted based on success/failure."""
        # Initialize a word
        update_progress("word1", True, self.progress, self.save_callback)
        initial_ef = self.progress["word1"]["easiness_factor"]

        # Success should increase the factor (but not above initial)
        update_progress("word1", True, self.progress, self.save_callback)
        self.assertEqual(
            self.progress["word1"]["easiness_factor"], initial_ef
        )  # Already at max

        # Failure should decrease the factor
        update_progress("word1", False, self.progress, self.save_callback)
        self.assertLess(self.progress["word1"]["easiness_factor"], initial_ef)

    def test_word_introduction_tracking(self):
        """Test that a word's first introduction date is recorded."""
        # Mock the current time to ensure stable test results
        mock_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=pytz.UTC)

        with patch(
            "vocabulary_learning.core.progress_tracking.get_utc_now",
            return_value=mock_time,
        ):
            # Initialize a new word
            update_progress("new_word", True, self.progress, self.save_callback)

            # Check that first_introduced date is set
            self.assertIn("first_introduced", self.progress["new_word"])
            self.assertEqual(
                self.progress["new_word"]["first_introduced"], mock_time.isoformat()
            )

            # Check is_newly_introduced returns True for a word with one attempt
            self.assertTrue(is_newly_introduced(self.progress["new_word"]))

            # Update the same word again
            later_time = mock_time + timedelta(days=1)
            with patch(
                "vocabulary_learning.core.progress_tracking.get_utc_now",
                return_value=later_time,
            ):
                update_progress("new_word", True, self.progress, self.save_callback)

                # Check first_introduced still has the original date
                self.assertEqual(
                    self.progress["new_word"]["first_introduced"], mock_time.isoformat()
                )

                # Check is_newly_introduced now returns False
                self.assertFalse(is_newly_introduced(self.progress["new_word"]))


if __name__ == "__main__":
    unittest.main()
