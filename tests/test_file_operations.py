"""Unit tests for file operations."""

import unittest
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
from rich.console import Console
from vocabulary_learning.core.file_operations import (
    load_vocabulary,
    load_progress,
    save_progress
)

class TestFileOperations(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.console = Console()
        self.temp_dir = tempfile.mkdtemp()
        self.vocab_file = os.path.join(self.temp_dir, 'vocabulary.json')
        self.progress_file = os.path.join(self.temp_dir, 'progress.json')
        
        # Mock Firebase reference
        self.mock_ref = MagicMock()
        
        # Sample vocabulary data
        self.vocab_data = {
            "word_000001": {
                "hiragana": "こんにちは",
                "kanji": "今日は",
                "french": "bonjour",
                "example_sentence": "こんにちは、元気ですか？"
            },
            "word_000002": {
                "hiragana": "さようなら",
                "kanji": "さようなら",
                "french": "au revoir",
                "example_sentence": ""
            }
        }
        
        # Sample progress data
        self.progress_data = {
            "こんにちは": {
                "attempts": 5,
                "successes": 4,
                "last_seen": datetime.now().isoformat(),
                "review_intervals": [1, 4, 24],
                "last_attempt_was_failure": False,
                "interval": 24
            }
        }

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.vocab_file):
            os.remove(self.vocab_file)
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        os.rmdir(self.temp_dir)

    def test_load_vocabulary_empty_file(self):
        """Test loading vocabulary from empty file."""
        vocabulary = load_vocabulary(self.vocab_file, self.mock_ref, self.console)
        self.assertIsInstance(vocabulary, pd.DataFrame)
        self.assertTrue(vocabulary.empty)

    def test_load_vocabulary_valid_data(self):
        """Test loading vocabulary with valid data."""
        with open(self.vocab_file, 'w', encoding='utf-8') as f:
            json.dump(self.vocab_data, f, ensure_ascii=False)
        
        vocabulary = load_vocabulary(self.vocab_file, self.mock_ref, self.console)
        self.assertEqual(len(vocabulary), 2)
        self.assertEqual(vocabulary.iloc[0]['japanese'], 'こんにちは')
        self.assertEqual(vocabulary.iloc[0]['french'], 'bonjour')

    def test_load_vocabulary_invalid_json(self):
        """Test loading vocabulary with invalid JSON."""
        with open(self.vocab_file, 'w', encoding='utf-8') as f:
            f.write('invalid json')
        
        vocabulary = load_vocabulary(self.vocab_file, self.mock_ref, self.console)
        self.assertTrue(vocabulary.empty)

    def test_load_progress_empty_file(self):
        """Test loading progress from empty file."""
        progress = load_progress(self.progress_file, None, self.console)
        self.assertEqual(progress, {})

    def test_load_progress_valid_data(self):
        """Test loading progress with valid data."""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress_data, f, ensure_ascii=False)
        
        progress = load_progress(self.progress_file, None, self.console)
        self.assertIn('こんにちは', progress)
        self.assertEqual(progress['こんにちは']['attempts'], 5)

    def test_load_progress_from_firebase(self):
        """Test loading progress from Firebase."""
        self.mock_ref.get.return_value = self.progress_data
        progress = load_progress(self.progress_file, self.mock_ref, self.console)
        self.assertEqual(progress, self.progress_data)
        self.mock_ref.get.assert_called_once()

    def test_load_progress_firebase_fallback(self):
        """Test fallback to local file when Firebase fails."""
        self.mock_ref.get.side_effect = Exception("Firebase error")
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress_data, f, ensure_ascii=False)
        
        progress = load_progress(self.progress_file, self.mock_ref, self.console)
        self.assertEqual(progress, self.progress_data)

    def test_save_progress_local(self):
        """Test saving progress to local file."""
        save_progress(self.progress_data, self.progress_file, None, self.console)
        
        with open(self.progress_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, self.progress_data)

    def test_save_progress_firebase(self):
        """Test saving progress to Firebase."""
        save_progress(self.progress_data, self.progress_file, self.mock_ref, self.console)
        self.mock_ref.set.assert_called_once_with(self.progress_data)

    def test_save_progress_firebase_failure(self):
        """Test handling Firebase save failure."""
        self.mock_ref.set.side_effect = Exception("Firebase error")
        
        # Should still save locally even if Firebase fails
        save_progress(self.progress_data, self.progress_file, self.mock_ref, self.console)
        
        with open(self.progress_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, self.progress_data)

if __name__ == '__main__':
    unittest.main() 