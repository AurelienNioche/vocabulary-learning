"""Unit tests for main module functionality."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from vocabulary_learning.main import VocabularyLearner


class TestVocabularyLearner(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.vocab_file = os.path.join(self.temp_dir, "vocabulary.json")
        self.progress_file = os.path.join(self.temp_dir, "progress.json")

        # Sample vocabulary data
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
                "last_seen": "2024-02-11T12:00:00",
            }
        }

        # Create environment variables for Firebase
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "FIREBASE_CREDENTIALS_PATH": os.path.join(
                    self.temp_dir, "firebase-credentials.json"
                ),
                "FIREBASE_DATABASE_URL": "https://test-db.firebaseio.com",
                "FIREBASE_USER_EMAIL": "test@example.com",
            },
        )
        self.env_patcher.start()

        # Create mock Firebase credentials file
        with open(os.environ["FIREBASE_CREDENTIALS_PATH"], "w") as f:
            f.write("{}")

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.vocab_file):
            os.remove(self.vocab_file)
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        if os.path.exists(os.environ["FIREBASE_CREDENTIALS_PATH"]):
            os.remove(os.environ["FIREBASE_CREDENTIALS_PATH"])
        os.rmdir(self.temp_dir)
        self.env_patcher.stop()

    @patch("firebase_admin.initialize_app")
    @patch("firebase_admin.credentials.Certificate")
    @patch("firebase_admin.auth.get_user_by_email")
    @patch("firebase_admin.db.reference")
    def test_learner_initialization_success(
        self, mock_db_ref, mock_get_user, mock_cert, mock_init_app
    ):
        """Test successful VocabularyLearner initialization."""
        # Mock user data
        mock_user = MagicMock()
        mock_user.uid = "test_user_id"
        mock_get_user.return_value = mock_user

        # Mock database references
        mock_progress_ref = MagicMock()
        mock_vocab_ref = MagicMock()
        mock_db_ref.side_effect = [mock_progress_ref, mock_vocab_ref]

        # Initialize learner
        learner = VocabularyLearner(
            vocab_file=self.vocab_file,
            progress_file=self.progress_file,
        )

        # Verify Firebase initialization
        mock_cert.assert_called_once()
        mock_init_app.assert_called_once()
        mock_get_user.assert_called_once_with("test@example.com")

        # Verify database references
        self.assertEqual(mock_db_ref.call_count, 2)
        self.assertIsNotNone(learner.progress_ref)
        self.assertIsNotNone(learner.vocab_ref)

        # Verify vim commands
        self.assertIn(":q", learner.vim_commands)
        self.assertIn(":h", learner.vim_commands)
        self.assertIn(":s", learner.vim_commands)

    @patch("firebase_admin.initialize_app")
    def test_learner_initialization_firebase_failure(self, mock_init_app):
        """Test VocabularyLearner initialization with Firebase failure."""
        # Make Firebase initialization fail
        mock_init_app.side_effect = Exception("Firebase connection failed")

        # Initialize learner
        learner = VocabularyLearner(
            vocab_file=self.vocab_file,
            progress_file=self.progress_file,
        )

        # Verify fallback to local storage
        self.assertIsNone(learner.progress_ref)
        self.assertIsNone(learner.vocab_ref)

    @patch("vocabulary_learning.main.save_progress")
    def test_save_progress(self, mock_save_progress):
        """Test progress saving."""
        # Initialize learner with mock Firebase
        with (
            patch("firebase_admin.initialize_app"),
            patch("firebase_admin.credentials.Certificate"),
            patch("firebase_admin.auth.get_user_by_email"),
            patch("firebase_admin.db.reference"),
        ):
            learner = VocabularyLearner(
                vocab_file=self.vocab_file,
                progress_file=self.progress_file,
            )

            # Set initial progress data
            learner.progress = self.progress

            # Save progress
            learner.save_progress()

            # Verify save was called
            mock_save_progress.assert_called_once_with(
                self.progress,
                learner.progress_file,
                learner.progress_ref,
                learner.console,
            )


if __name__ == "__main__":
    unittest.main()
