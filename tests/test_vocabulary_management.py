"""Unit tests for vocabulary management functionality."""

import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
from rich.console import Console

from vocabulary_learning.core.vocabulary_management import add_vocabulary, reset_progress


class TestVocabularyManagement(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.console = Console()
        self.temp_dir = tempfile.mkdtemp()
        self.vocab_file = os.path.join(self.temp_dir, "vocabulary.json")
        self.progress_file = os.path.join(self.temp_dir, "progress.json")

        # Create empty vocabulary DataFrame
        self.vocabulary = pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])

        # Sample progress data
        self.progress = {
            "こんにちは": {
                "attempts": 5,
                "successes": 4,
                "last_seen": datetime.now().isoformat(),
            }
        }

        # Mock Firebase reference
        self.mock_ref = MagicMock()

        # Mock JapaneseTextConverter
        self.mock_converter = MagicMock()
        self.mock_converter.to_hiragana.return_value = "ひらがな"
        self.mock_converter.to_katakana.return_value = "カタカナ"
        self.mock_converter.to_romaji.return_value = "romaji"

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.vocab_file):
            os.remove(self.vocab_file)
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        # Clean up backup files
        for f in os.listdir(self.temp_dir):
            if f.startswith("progress.json.backup"):
                os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    @patch("builtins.input")
    def test_add_vocabulary_success(self, mock_input):
        """Test adding new vocabulary successfully."""
        # Mock user inputs
        mock_input.side_effect = [
            "あたらしい",  # Japanese
            "新しい",  # Kanji
            "nouveau",  # French
            "新しい車を買いました。",  # Example
            "n",  # Don't add another word
        ]

        # Create a mock vocabulary DataFrame
        mock_vocab_df = pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])
        mock_load_vocab = MagicMock(return_value=mock_vocab_df)

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(
                mock_vocab_df,
                self.vocab_file,
                self.mock_ref,
                self.console,
                mock_load_vocab,
                japanese_converter=self.mock_converter,
            )

        # Verify file was created
        self.assertTrue(os.path.exists(self.vocab_file))

        # Check file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify word was added
        self.assertEqual(len(vocab_data), 1)
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "ひらがな")
        self.assertEqual(vocab_data[word_id]["kanji"], "新しい")
        self.assertEqual(vocab_data[word_id]["french"], "nouveau")
        self.assertEqual(vocab_data[word_id]["example_sentence"], "新しい車を買いました。")

        # Verify Firebase sync
        self.mock_ref.set.assert_called_once_with(vocab_data)

        # Verify load_vocabulary was called
        mock_load_vocab.assert_called_once()

        # Verify converter was called
        self.mock_converter.to_hiragana.assert_called_once_with("あたらしい")

    @patch("builtins.input")
    @patch("rich.prompt.Confirm.ask", return_value=False)
    def test_add_vocabulary_duplicate(self, mock_confirm, mock_input):
        """Test adding duplicate vocabulary."""
        # Create existing vocabulary file
        with open(self.vocab_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "word_000001": {
                        "hiragana": "あたらしい",
                        "kanji": "新しい",
                        "french": "nouveau",
                        "example_sentence": "",
                    }
                },
                f,
            )

        # Mock user inputs - provide enough inputs for both the duplicate case and a new word
        mock_input.side_effect = [
            "あたらしい",  # Japanese (duplicate)
            ":m",  # Return to menu after duplicate is detected
        ]

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        # Create DataFrame with existing word
        vocabulary = pd.DataFrame([{"japanese": "あたらしい"}])

        add_vocabulary(
            vocabulary,
            self.vocab_file,
            None,
            self.console,
            mock_load_vocab,
        )

        # Verify file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify word was not added again
        self.assertEqual(len(vocab_data), 1)
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "あたらしい")

    @patch("builtins.input")
    def test_add_vocabulary_missing_required_fields(self, mock_input):
        """Test adding vocabulary with missing required fields."""
        # Mock user inputs
        mock_input.side_effect = [
            "あたらしい",  # Japanese
            "",  # Kanji (empty)
            "",  # French (empty)
            ":m",  # Return to menu after French validation error
        ]

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        add_vocabulary(
            self.vocabulary,
            self.vocab_file,
            None,
            self.console,
            mock_load_vocab,
        )

        # Verify no file was created for invalid input
        self.assertFalse(os.path.exists(self.vocab_file))

    @patch("builtins.input")
    def test_add_vocabulary_firebase_sync_failure(self, mock_input):
        """Test adding vocabulary with Firebase sync failure."""
        # Mock user inputs
        mock_input.side_effect = [
            "あたらしい",  # Japanese
            "新しい",  # Kanji
            "nouveau",  # French
            "",  # Example (empty)
            "n",  # Don't add another word
        ]

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        # Make Firebase sync fail
        mock_ref = MagicMock()
        mock_ref.set.side_effect = Exception("Firebase sync failed")

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(
                self.vocabulary,
                self.vocab_file,
                mock_ref,
                self.console,
                mock_load_vocab,
            )

        # Verify file was still created locally
        self.assertTrue(os.path.exists(self.vocab_file))

    @patch("rich.prompt.Confirm.ask")
    def test_reset_progress_confirmed(self, mock_confirm):
        """Test resetting progress with confirmation."""
        # Create progress file
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f)

        # Mock confirmation
        mock_confirm.return_value = True

        # Mock save callback
        mock_save = MagicMock()

        reset_progress(self.progress_file, self.mock_ref, self.progress, mock_save, self.console)

        # Verify progress was cleared
        self.assertEqual(len(self.progress), 0)
        mock_save.assert_called_once()

        # Verify backup was created
        backup_files = [
            f for f in os.listdir(self.temp_dir) if f.startswith("progress.json.backup")
        ]
        self.assertEqual(len(backup_files), 1)

        # Verify Firebase was reset
        self.mock_ref.set.assert_called_once_with({})

    @patch("rich.prompt.Confirm.ask")
    def test_reset_progress_cancelled(self, mock_confirm):
        """Test cancelling progress reset."""
        # Create progress file
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f)

        # Mock confirmation
        mock_confirm.return_value = False

        # Mock save callback
        mock_save = MagicMock()

        reset_progress(self.progress_file, self.mock_ref, self.progress, mock_save, self.console)

        # Verify progress was not cleared
        self.assertEqual(len(self.progress), 1)
        mock_save.assert_not_called()

        # Verify no backup was created
        backup_files = [
            f for f in os.listdir(self.temp_dir) if f.startswith("progress.json.backup")
        ]
        self.assertEqual(len(backup_files), 0)

        # Verify Firebase was not reset
        self.mock_ref.set.assert_not_called()

    @patch("rich.prompt.Confirm.ask")
    def test_reset_progress_firebase_failure(self, mock_confirm):
        """Test resetting progress with Firebase failure."""
        # Create progress file
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.progress, f)

        # Mock confirmation
        mock_confirm.return_value = True

        # Mock save callback
        mock_save = MagicMock()

        # Make Firebase reset fail
        mock_ref = MagicMock()
        mock_ref.set.side_effect = Exception("Firebase reset failed")

        reset_progress(self.progress_file, mock_ref, self.progress, mock_save, self.console)

        # Verify progress was still cleared locally
        self.assertEqual(len(self.progress), 0)
        mock_save.assert_called_once()

        # Verify backup was created
        backup_files = [
            f for f in os.listdir(self.temp_dir) if f.startswith("progress.json.backup")
        ]
        self.assertEqual(len(backup_files), 1)

    @patch("builtins.input")
    def test_add_vocabulary_with_old_format(self, mock_input):
        """Test adding vocabulary when existing file uses old list format."""
        # Create existing vocabulary file with old list format
        with open(self.vocab_file, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "japanese": "こんにちは",
                        "kanji": "今日は",
                        "french": "bonjour",
                        "example_sentence": "",
                    }
                ],
                f,
            )

        # Mock user inputs
        mock_input.side_effect = [
            "さっき",  # Japanese
            "",  # Kanji (empty)
            "à l'instant",  # French
            "",  # Example (empty)
            "n",  # Don't add another word
        ]

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(
                self.vocabulary,
                self.vocab_file,
                None,
                self.console,
                mock_load_vocab,
            )

        # Verify file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify both words are present in dictionary format
        self.assertEqual(len(vocab_data), 2)
        self.assertTrue(isinstance(vocab_data, dict))
        self.assertTrue(any(word["hiragana"] == "こんにちは" for word in vocab_data.values()))
        self.assertTrue(any(word["hiragana"] == "さっき" for word in vocab_data.values()))

    @patch("builtins.input")
    def test_add_vocabulary_with_invalid_format(self, mock_input):
        """Test adding vocabulary when existing file has invalid format."""
        # Create existing vocabulary file with invalid format (not a dict)
        with open(self.vocab_file, "w", encoding="utf-8") as f:
            json.dump(["some", "invalid", "data"], f)

        # Mock user inputs
        mock_input.side_effect = [
            "さっき",  # Japanese
            "",  # Kanji (empty)
            "à l'instant",  # French
            "",  # Example (empty)
            "n",  # Don't add another word
        ]

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(
                self.vocabulary,
                self.vocab_file,
                None,
                self.console,
                mock_load_vocab,
            )

        # Verify file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify the word was added to a fresh dictionary
        self.assertEqual(len(vocab_data), 1)
        self.assertTrue(isinstance(vocab_data, dict))
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "さっき")
        self.assertEqual(vocab_data[word_id]["french"], "à l'instant")

    @patch("builtins.input")
    def test_add_vocabulary_empty_initial(self, mock_input):
        """Test adding vocabulary when starting with empty vocabulary."""
        # Mock user inputs
        mock_input.side_effect = [
            "あたらしい",  # Japanese
            "新しい",  # Kanji
            "nouveau",  # French
            "",  # Example (empty)
            "n",  # Don't add another word
        ]

        # Create empty vocabulary DataFrame
        empty_vocabulary = pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])

        # Mock load_vocabulary function
        mock_load_vocab = MagicMock()

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(
                empty_vocabulary,
                self.vocab_file,
                None,
                self.console,
                mock_load_vocab,
            )

        # Verify file was created
        self.assertTrue(os.path.exists(self.vocab_file))

        # Check file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify word was added
        self.assertEqual(len(vocab_data), 1)
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "あたらしい")
        self.assertEqual(vocab_data[word_id]["kanji"], "新しい")
        self.assertEqual(vocab_data[word_id]["french"], "nouveau")
        self.assertEqual(vocab_data[word_id]["example_sentence"], "")

    @patch("builtins.input")
    def test_add_vocabulary_quit_command(self, mock_input):
        """Test quitting from add vocabulary mode."""
        mock_input.side_effect = [":q"]  # Quit immediately

        with self.assertRaises(SystemExit):
            add_vocabulary(
                self.vocabulary,
                self.vocab_file,
                None,
                self.console,
                MagicMock(),
            )

    @patch("builtins.input")
    def test_add_vocabulary_menu_command(self, mock_input):
        """Test returning to menu from add vocabulary mode."""
        mock_input.side_effect = [":m"]  # Return to menu immediately

        # Should return without raising any exceptions
        add_vocabulary(
            self.vocabulary,
            self.vocab_file,
            None,
            self.console,
            MagicMock(),
        )

    @patch("builtins.input")
    def test_add_vocabulary_load_error(self, mock_input):
        """Test handling load_vocabulary function error."""
        mock_input.side_effect = [
            "あたらしい",  # Japanese
            "新しい",  # Kanji
            "nouveau",  # French
            "",  # Example
            "n",  # Don't add another word
        ]

        # Mock load_vocabulary function that raises an error
        mock_load_vocab = MagicMock(side_effect=Exception("Load error"))

        with patch("rich.prompt.Confirm.ask", return_value=False):
            # Should continue despite load error
            add_vocabulary(
                self.vocabulary,
                self.vocab_file,
                None,
                self.console,
                mock_load_vocab,
            )

        # Verify file was still created
        self.assertTrue(os.path.exists(self.vocab_file))

        # Check file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify word was added despite load error
        self.assertEqual(len(vocab_data), 1)
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "あたらしい")

    @patch("builtins.input")
    def test_add_vocabulary_command_handling(self, mock_input):
        """Test command handling in add vocabulary mode."""
        test_cases = [
            (
                ":h",
                None,
                ["あたらしい", "新しい", "nouveau", "", ":m"],
            ),  # Help command should continue execution
            (":m", None, []),  # Menu command should exit normally
            (":q", SystemExit, []),  # Quit command should raise SystemExit
            ("", None, [":m"]),  # Empty input should continue
        ]

        for command, expected_exception, additional_inputs in test_cases:
            mock_input.reset_mock()
            mock_input.side_effect = [command] + additional_inputs

            mock_vocab_df = pd.DataFrame(
                columns=["japanese", "kanji", "french", "example_sentence"]
            )
            mock_load_vocab = MagicMock()

            if expected_exception:
                with self.assertRaises(expected_exception):
                    add_vocabulary(
                        mock_vocab_df,
                        self.vocab_file,
                        None,
                        self.console,
                        mock_load_vocab,
                    )
            else:
                with patch("rich.prompt.Confirm.ask", return_value=False):
                    add_vocabulary(
                        mock_vocab_df,
                        self.vocab_file,
                        None,
                        self.console,
                        mock_load_vocab,
                    )

            # Verify load_vocabulary was not called for commands
            if command in [":m", ":q", ""]:
                mock_load_vocab.assert_not_called()
            elif command == ":h":
                # For help command, we continue with a word addition
                self.assertEqual(mock_load_vocab.call_count, 1)

    @patch("builtins.input")
    def test_add_vocabulary_multiple_words(self, mock_input):
        """Test adding multiple vocabulary words in one session."""
        # Mock user inputs for two words
        mock_input.side_effect = [
            # First word
            "あたらしい",  # Japanese
            "新しい",  # Kanji
            "nouveau",  # French
            "",  # Example
            # Second word
            "こんにちは",  # Japanese
            "今日は",  # Kanji
            "bonjour",  # French
            "こんにちは、元気ですか",  # Example
            # Third attempt (to exit)
            ":m",  # Return to menu
        ]

        # Create mock vocabulary DataFrames for each state
        initial_vocab_df = pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])
        first_word_df = pd.DataFrame(
            [
                {
                    "japanese": "あたらしい",
                    "kanji": "新しい",
                    "french": "nouveau",
                    "example_sentence": "",
                    "word_id": "word_000001",
                }
            ]
        )

        # Mock load_vocabulary to return updated DataFrames
        mock_load_vocab = MagicMock(
            side_effect=[first_word_df, first_word_df]
        )  # Called twice, once for each word

        # Mock Confirm.ask to return True for first word, False for second
        with patch("rich.prompt.Confirm.ask", side_effect=[True, False]):
            add_vocabulary(
                initial_vocab_df,
                self.vocab_file,
                None,
                self.console,
                mock_load_vocab,
            )

        # Verify file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify both words were added
        self.assertEqual(len(vocab_data), 2)
        self.assertTrue(any(word["hiragana"] == "あたらしい" for word in vocab_data.values()))
        self.assertTrue(any(word["hiragana"] == "こんにちは" for word in vocab_data.values()))

        # Verify load_vocabulary was called twice (once after each word)
        self.assertEqual(mock_load_vocab.call_count, 2)

    @patch("builtins.input")
    def test_add_vocabulary_empty_japanese(self, mock_input):
        """Test handling empty Japanese input."""
        mock_input.side_effect = [
            "",  # Empty Japanese
            ":m",  # Return to menu
        ]

        add_vocabulary(
            self.vocabulary,
            self.vocab_file,
            None,
            self.console,
            MagicMock(),
        )

        # Verify no file was created for empty input
        self.assertFalse(os.path.exists(self.vocab_file))

    @patch("builtins.input")
    def test_add_vocabulary_empty_french(self, mock_input):
        """Test handling empty French input."""
        mock_input.side_effect = [
            "あたらしい",  # Japanese
            "新しい",  # Kanji
            "",  # Empty French
            ":m",  # Return to menu
        ]

        add_vocabulary(
            self.vocabulary,
            self.vocab_file,
            None,
            self.console,
            MagicMock(),
        )

        # Verify no file was created for empty French
        self.assertFalse(os.path.exists(self.vocab_file))

    @patch("builtins.input")
    def test_add_vocabulary_reload_failure(self, mock_input):
        """Test handling vocabulary reload failure."""
        # Mock user inputs
        mock_input.side_effect = [
            "あたらしい",  # Japanese
            "新しい",  # Kanji
            "nouveau",  # French
            "",  # Example
            "n",  # Don't add another word
        ]

        # Create a mock vocabulary DataFrame
        mock_vocab_df = pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])
        mock_load_vocab = MagicMock(side_effect=Exception("Load error"))

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(
                mock_vocab_df,
                self.vocab_file,
                None,
                self.console,
                mock_load_vocab,
            )

        # Verify file was created despite load error
        self.assertTrue(os.path.exists(self.vocab_file))

        # Check file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify word was added despite load error
        self.assertEqual(len(vocab_data), 1)
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "あたらしい")

        # Verify load_vocabulary was called
        mock_load_vocab.assert_called_once()

    @patch("builtins.input")
    def test_add_vocabulary_with_conversion(self, mock_input):
        """Test adding vocabulary with text conversion."""
        # Mock user inputs
        mock_input.side_effect = [
            "にほんてき",  # Japanese
            "日本的",  # Kanji
            "style japonais",  # French
            "",  # Example
            "n",  # Don't add another word
        ]

        # Create a mock vocabulary DataFrame
        mock_vocab_df = pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])
        mock_load_vocab = MagicMock(return_value=mock_vocab_df)

        # Mock JapaneseTextConverter
        mock_converter = MagicMock()
        mock_converter.to_hiragana.return_value = "にほんてき"
        mock_converter.to_katakana.return_value = "ニホンテキ"
        mock_converter.to_romaji.return_value = "nihonteki"

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(
                mock_vocab_df,
                self.vocab_file,
                None,
                self.console,
                mock_load_vocab,
                japanese_converter=mock_converter,
            )

        # Verify file was created
        self.assertTrue(os.path.exists(self.vocab_file))

        # Check file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify word was added with correct conversions
        self.assertEqual(len(vocab_data), 1)
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "にほんてき")
        self.assertEqual(vocab_data[word_id]["kanji"], "日本的")
        self.assertEqual(vocab_data[word_id]["french"], "style japonais")

        # Verify converter methods were called
        mock_converter.to_hiragana.assert_called_once_with("にほんてき")

        # Verify load_vocabulary was called
        mock_load_vocab.assert_called_once()

    @patch("builtins.input")
    def test_add_vocabulary_converter_failure(self, mock_input):
        """Test handling Japanese text converter failure."""
        # Mock user inputs
        mock_input.side_effect = [
            "にほんてき",  # Japanese
            "日本的",  # Kanji
            "style japonais",  # French
            "",  # Example
            "n",  # Don't add another word
        ]

        # Create a mock vocabulary DataFrame
        mock_vocab_df = pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])
        mock_load_vocab = MagicMock(return_value=mock_vocab_df)

        # Mock converter that raises an exception
        mock_converter = MagicMock()
        mock_converter.to_hiragana.side_effect = Exception("Conversion failed")

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(
                mock_vocab_df,
                self.vocab_file,
                None,
                self.console,
                mock_load_vocab,
                japanese_converter=mock_converter,
            )

        # Verify file was created despite conversion error
        self.assertTrue(os.path.exists(self.vocab_file))

        # Check file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify word was added with original input
        self.assertEqual(len(vocab_data), 1)
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "にほんてき")  # Original input preserved
        self.assertEqual(vocab_data[word_id]["kanji"], "日本的")
        self.assertEqual(vocab_data[word_id]["french"], "style japonais")

        # Verify converter was called
        mock_converter.to_hiragana.assert_called_once_with("にほんてき")

        # Verify load_vocabulary was called
        mock_load_vocab.assert_called_once()

    @patch("builtins.input")
    def test_add_vocabulary_proper_reload(self, mock_input):
        """Test that load_vocabulary is called with correct parameters."""
        # Mock user inputs
        mock_input.side_effect = [
            "あたらしい",  # Japanese
            "新しい",  # Kanji
            "nouveau",  # French
            "",  # Example
            "n",  # Don't add another word
        ]

        # Create a mock vocabulary DataFrame
        mock_vocab_df = pd.DataFrame(columns=["japanese", "kanji", "french", "example_sentence"])

        # Create a mock load_vocabulary function that verifies its arguments
        def verify_load_vocab(file, ref, console):
            self.assertEqual(file, self.vocab_file)
            self.assertEqual(ref, None)
            self.assertIsInstance(console, Console)
            return mock_vocab_df

        mock_load_vocab = MagicMock(side_effect=verify_load_vocab)

        with patch("rich.prompt.Confirm.ask", return_value=False):
            add_vocabulary(
                mock_vocab_df,
                self.vocab_file,
                None,
                self.console,
                mock_load_vocab,
                japanese_converter=self.mock_converter,
            )

        # Verify load_vocabulary was called once
        mock_load_vocab.assert_called_once()

        # Verify file was created
        self.assertTrue(os.path.exists(self.vocab_file))

        # Check file contents
        with open(self.vocab_file, "r", encoding="utf-8") as f:
            vocab_data = json.load(f)

        # Verify word was added
        self.assertEqual(len(vocab_data), 1)
        word_id = list(vocab_data.keys())[0]
        self.assertEqual(vocab_data[word_id]["hiragana"], "ひらがな")
        self.assertEqual(vocab_data[word_id]["kanji"], "新しい")
        self.assertEqual(vocab_data[word_id]["french"], "nouveau")


if __name__ == "__main__":
    unittest.main()
