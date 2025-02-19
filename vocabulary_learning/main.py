"""Main entry point for the vocabulary learning tool."""

import os
import signal
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from vocabulary_learning.core.constants import ENV_FILE
from vocabulary_learning.core.file_operations import load_progress, load_vocabulary, save_progress
from vocabulary_learning.core.firebase_config import initialize_firebase
from vocabulary_learning.core.japanese_utils import JapaneseTextConverter
from vocabulary_learning.core.practice import practice_mode
from vocabulary_learning.core.progress_tracking import update_progress
from vocabulary_learning.core.ui_components import show_help, show_progress, show_word_statistics
from vocabulary_learning.core.utils import get_data_dir, signal_handler
from vocabulary_learning.core.vocabulary_management import add_vocabulary, reset_progress

# Get the package root directory
PACKAGE_ROOT = Path(__file__).parent

#######################
# Main Learner Class #
#######################


class VocabularyLearner:
    def __init__(
        self,
        vocab_file=None,
        progress_file=None,
    ):
        # Get OS-specific data directory
        data_dir = Path(get_data_dir()) / "data"

        # Set default file paths if not provided
        self.vocab_file = str(vocab_file or data_dir / "vocabulary.json")
        self.progress_file = str(progress_file or data_dir / "progress.json")

        # Ensure data directory exists
        data_dir.mkdir(parents=True, exist_ok=True)

        self.console = Console()

        # Initialize Firebase
        load_dotenv(Path(get_data_dir()) / ENV_FILE)
        self.progress_ref, self.vocab_ref = initialize_firebase(
            console=self.console, env_file=str(Path(get_data_dir()) / ENV_FILE)
        )

        # Initialize components
        self.japanese_converter = JapaneseTextConverter()

        # Load data
        self.vocabulary = load_vocabulary(self.vocab_file, self.vocab_ref, self.console)
        self.progress = load_progress(self.progress_file, self.progress_ref, self.console)

        # Setup signal handler for graceful exit
        signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, self.save_progress))

        # Initialize commands
        self.vim_commands = {
            ":q": "quit program",
            ":m": "return to menu",
            ":h": "show help",
            ":s": "show word statistics",
            ":e": "show example",
            ":d": "show answer (don't know)",
        }

        self.last_save_time = datetime.now()

    def save_progress(self):
        """Save learning progress to Firebase and local backup."""
        save_progress(self.progress, self.progress_file, self.progress_ref, self.console)

    def run(self):
        """Run the main program loop."""
        # Show data directory location
        self.console.print(f"\n[dim]Data directory: {Path(get_data_dir())}[/dim]")

        # Start directly in practice mode
        practice_mode(
            self.vocabulary,
            self.progress,
            self.console,
            self.japanese_converter,
            lambda word_id, success: update_progress(
                word_id, success, self.progress, self.save_progress
            ),
            lambda: show_help(self.vim_commands, self.console),
            lambda word_id: show_word_statistics(
                (word_id, self.vocabulary[word_id]), self.progress, self.console
            ),
            self.save_progress,
        )

        # Continue with menu loop
        while True:
            self.console.print("\n[bold blue]Japanese Vocabulary Learning[/bold blue]")
            self.console.print()  # Add empty line
            self.console.print("[dim]Available commands:[/dim]")
            self.console.print("[blue]:q[/blue] quit")
            self.console.print()  # Add empty line
            self.console.print("1. Practice vocabulary")
            self.console.print("2. Show progress")
            self.console.print("3. Add vocabulary")
            self.console.print("4. Reset progress")

            choice = input("\nEnter your choice: ").strip()

            if choice.lower() == ":q":
                self.console.print()  # Add empty line
                self.save_progress()
                break
            elif choice == "1":
                practice_mode(
                    self.vocabulary,
                    self.progress,
                    self.console,
                    self.japanese_converter,
                    lambda word_id, success: update_progress(
                        word_id, success, self.progress, self.save_progress
                    ),
                    lambda: show_help(self.vim_commands, self.console),
                    lambda word_id: show_word_statistics(
                        (word_id, self.vocabulary[word_id]), self.progress, self.console
                    ),
                    self.save_progress,
                )
            elif choice == "2":
                show_progress(self.vocabulary, self.progress, self.console)
            elif choice == "3":
                add_vocabulary(
                    vocabulary=self.vocabulary,
                    vocab_file=self.vocab_file,
                    vocab_ref=self.vocab_ref,
                    console=self.console,
                    load_vocabulary=load_vocabulary,
                    japanese_converter=self.japanese_converter,
                    vim_commands=self.vim_commands,
                )
            elif choice == "4":
                reset_progress(self.progress_file, self.progress_ref, self.console)
                self.progress = {}
            else:
                self.console.print("[red]Invalid choice. Please try again.[/red]")


def main():
    """Start the vocabulary learning tool."""
    learner = VocabularyLearner()
    learner.run()


if __name__ == "__main__":
    main()
