"""Test cases for the main module."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from rich.console import Console

from vocabulary_learning.core.file_operations import load_vocabulary
from vocabulary_learning.main import VocabularyLearner


class TestVocabularyLearner(unittest.TestCase):
    """Test cases for VocabularyLearner class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        self.vocab_file = str(self.data_dir / "vocabulary.json")
        self.progress_file = str(self.data_dir / "progress.json")
        self.env_file = str(Path(self.temp_dir) / ".env")

        # Create empty files
        for file in [self.vocab_file, self.progress_file]:
            with open(file, "w") as f:
                f.write("{}")

        # Create .env file with test values
        with open(self.env_file, "w") as f:
            f.write("FIREBASE_CREDENTIALS_PATH=test_creds.json\n")
            f.write("FIREBASE_DATABASE_URL=https://test.firebaseio.com\n")
            f.write("FIREBASE_USER_EMAIL=test@example.com\n")
            f.write("TIMEZONE=UTC\n")

    def tearDown(self):
        """Clean up test environment."""
        # Remove test files
        for file in [self.vocab_file, self.progress_file, self.env_file]:
            if os.path.exists(file):
                os.remove(file)
        # Remove test directories
        if os.path.exists(self.data_dir):
            os.rmdir(self.data_dir)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    @patch("vocabulary_learning.main.initialize_firebase")
    @patch("vocabulary_learning.main.get_data_dir")
    def test_learner_initialization_success(self, mock_get_data_dir, mock_init_firebase):
        """Test successful VocabularyLearner initialization."""
        # Mock get_data_dir to return our temp directory
        mock_get_data_dir.return_value = self.temp_dir

        # Mock Firebase initialization
        mock_progress_ref = MagicMock()
        mock_vocab_ref = MagicMock()
        mock_init_firebase.return_value = (mock_progress_ref, mock_vocab_ref)

        # Initialize learner
        learner = VocabularyLearner(
            vocab_file=self.vocab_file,
            progress_file=self.progress_file,
        )

        # Verify learner is initialized correctly
        self.assertIsNotNone(learner.console)
        self.assertEqual(learner.vocab_file, self.vocab_file)
        self.assertEqual(learner.progress_file, self.progress_file)

    @patch("vocabulary_learning.main.save_progress")
    @patch("vocabulary_learning.main.get_data_dir")
    def test_save_progress(self, mock_get_data_dir, mock_save_progress):
        """Test progress saving."""
        # Mock get_data_dir to return our temp directory
        mock_get_data_dir.return_value = self.temp_dir

        # Initialize learner with mock Firebase
        with patch("vocabulary_learning.main.initialize_firebase") as mock_init_firebase:
            mock_progress_ref = MagicMock()
            mock_vocab_ref = MagicMock()
            mock_init_firebase.return_value = (mock_progress_ref, mock_vocab_ref)

            learner = VocabularyLearner(
                vocab_file=self.vocab_file,
                progress_file=self.progress_file,
            )

            # Set initial progress data
            learner.progress = {}

            # Save progress
            learner.save_progress()

            # Verify save was called
            mock_save_progress.assert_called_once_with(
                {},
                learner.progress_file,
                learner.progress_ref,
                learner.console,
            )

    @patch("vocabulary_learning.main.practice_mode")
    @patch("vocabulary_learning.main.add_vocabulary")
    @patch("vocabulary_learning.main.save_progress")
    @patch("vocabulary_learning.main.initialize_firebase")
    @patch("vocabulary_learning.main.get_data_dir")
    def test_menu_add_vocabulary(
        self,
        mock_get_data_dir,
        mock_init_firebase,
        mock_save_progress,
        mock_add_vocab,
        mock_practice,
    ):
        """Test menu option for adding vocabulary."""
        # Mock get_data_dir to return our temp directory
        mock_get_data_dir.return_value = self.temp_dir

        # Mock Firebase initialization
        mock_progress_ref = MagicMock()
        mock_vocab_ref = MagicMock()
        mock_init_firebase.return_value = (mock_progress_ref, mock_vocab_ref)

        # Initialize learner
        learner = VocabularyLearner(
            vocab_file=self.vocab_file,
            progress_file=self.progress_file,
        )

        # Mock input to select "Add vocabulary" then "Quit"
        with patch("builtins.input", side_effect=["3", ":q"]):
            learner.run()

            # Verify add_vocabulary was called with correct parameters
            mock_add_vocab.assert_called_once_with(
                vocabulary=learner.vocabulary,
                vocab_file=learner.vocab_file,
                vocab_ref=learner.vocab_ref,
                console=learner.console,
                load_vocabulary=load_vocabulary,
                japanese_converter=learner.japanese_converter,
                vim_commands=learner.vim_commands,
            )


if __name__ == "__main__":
    unittest.main()
