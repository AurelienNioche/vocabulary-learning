"""Unit tests for progress tracking functionality."""

import unittest
from datetime import datetime, timedelta
from vocabulary_learning.core.progress_tracking import (
    update_progress,
    calculate_priority,
    count_active_learning_words
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
        update_progress("新しい", False, self.progress, self.save_callback)
        
        self.assertIn("新しい", self.progress)
        word_data = self.progress["新しい"]
        self.assertEqual(word_data['attempts'], 1)
        self.assertEqual(word_data['successes'], 0)
        self.assertEqual(word_data['interval'], 4)  # Failed attempt sets to minimum 4
        self.assertTrue(word_data['last_attempt_was_failure'])
        self.assertTrue(self.save_called)

    def test_interval_progression(self):
        """Test interval progression for successful attempts."""
        word = "テスト"
        
        # First attempt (success)
        update_progress(word, True, self.progress, self.save_callback)
        self.assertEqual(self.progress[word]['interval'], 4)
        
        # Second attempt (success)
        update_progress(word, True, self.progress, self.save_callback)
        self.assertEqual(self.progress[word]['interval'], 24)
        
        # Third attempt (success) - should use easiness factor
        initial_interval = self.progress[word]['interval']
        easiness = self.progress[word]['easiness_factor']
        update_progress(word, True, self.progress, self.save_callback)
        self.assertEqual(self.progress[word]['interval'], initial_interval * easiness)

    def test_failed_attempt(self):
        """Test interval reduction on failed attempt."""
        word = "失敗"
        
        # First success to set initial interval
        update_progress(word, True, self.progress, self.save_callback)
        initial_interval = self.progress[word]['interval']
        
        # Failed attempt
        update_progress(word, False, self.progress, self.save_callback)
        self.assertEqual(self.progress[word]['interval'], max(4, initial_interval * 0.5))
        self.assertTrue(self.progress[word]['last_attempt_was_failure'])

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
            'successes': 4,
            'attempts': 5,
            'interval': 4,
            'last_seen': (datetime.now() - timedelta(hours=8)).isoformat(),
            'last_attempt_was_failure': True
        }
        
        priority = calculate_priority(word_data, active_words_count=5)
        
        # Priority should be non-zero (word is overdue)
        self.assertGreater(priority, 0)
        # Priority should include failure bonus
        self.assertGreaterEqual(priority, 0.3)

    def test_count_active_learning_words(self):
        """Test counting active learning words."""
        progress = {
            'word1': {'attempts': 10, 'successes': 9},  # 90% - mastered
            'word2': {'attempts': 10, 'successes': 7},  # 70% - active
            'word3': {'attempts': 5, 'successes': 2},   # 40% - active
            'word4': {'attempts': 0, 'successes': 0}    # new word - not active
        }
        
        active_count = count_active_learning_words(progress)
        self.assertEqual(active_count, 2)

    def test_review_intervals_tracking(self):
        """Test tracking of review intervals."""
        word = "間隔"
        
        # First attempt
        update_progress(word, True, self.progress, self.save_callback)
        self.assertEqual(len(self.progress[word]['review_intervals']), 1)
        
        # Simulate time passing
        self.progress[word]['last_seen'] = (datetime.now() - timedelta(hours=2)).isoformat()
        
        # Second attempt
        update_progress(word, True, self.progress, self.save_callback)
        self.assertEqual(len(self.progress[word]['review_intervals']), 2)
        self.assertAlmostEqual(self.progress[word]['review_intervals'][-1], 2, delta=0.1)

    def test_easiness_factor_adjustment(self):
        """Test adjustment of easiness factor."""
        word = "簡単"
        
        # Initial easiness factor
        update_progress(word, True, self.progress, self.save_callback)
        initial_ef = self.progress[word]['easiness_factor']
        
        # Success increases EF
        update_progress(word, True, self.progress, self.save_callback)
        self.assertGreater(self.progress[word]['easiness_factor'], initial_ef)
        
        # Failure decreases EF
        ef_before_failure = self.progress[word]['easiness_factor']
        update_progress(word, False, self.progress, self.save_callback)
        self.assertLess(self.progress[word]['easiness_factor'], ef_before_failure)
        
        # EF should not go below 1.3
        for _ in range(5):  # Multiple failures
            update_progress(word, False, self.progress, self.save_callback)
        self.assertGreaterEqual(self.progress[word]['easiness_factor'], 1.3)

if __name__ == '__main__':
    unittest.main() 