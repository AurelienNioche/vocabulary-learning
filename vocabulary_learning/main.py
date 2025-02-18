"""Main entry point for the vocabulary learning tool."""

import os
import signal
import sys
from datetime import datetime
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import auth, credentials, db
from rich.console import Console
from rich.prompt import Confirm

from vocabulary_learning.core.file_operations import load_progress, load_vocabulary, save_progress
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
        load_dotenv(Path(get_data_dir()) / ".env")
        cred_path = os.path.expandvars(os.getenv("FIREBASE_CREDENTIALS_PATH"))

        if not os.path.exists(cred_path):
            self.console.print(f"[red]Error: Firebase credentials not found at {cred_path}[/red]")
            exit(1)

        try:
            try:
                firebase_admin.get_app()
                self.console.print("[dim]Using existing Firebase connection[/dim]")
            except ValueError:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(
                    cred, {"databaseURL": os.getenv("FIREBASE_DATABASE_URL")}
                )

            # Get user credentials
            email = os.getenv("FIREBASE_USER_EMAIL")
            if not email:
                raise ValueError("Firebase user email not found in .env")

            # Get user ID
            user = auth.get_user_by_email(email)
            user_id = user.uid
            self.console.print(f"[dim]Authenticated as: {email}[/dim]")

            # Set up database references
            self.progress_ref = db.reference(f"/progress/{user_id}")
            self.vocab_ref = db.reference(f"/vocabulary/{user_id}")
            self.console.print("[green]Successfully connected to Firebase![/green]")

        except Exception as e:
            self.console.print(f"[red]Failed to initialize Firebase: {str(e)}[/red]")
            self.progress_ref = None
            self.vocab_ref = None
            self.console.print("[yellow]Falling back to local storage...[/yellow]")

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
            ":S": "show all statistics",
            ":e": "show example",
            ":d": "show answer (don't know)",
        }

        self.last_save_time = datetime.now()

    def save_progress(self):
        """Save learning progress to Firebase and local backup."""
        save_progress(self.progress, self.progress_file, self.progress_ref, self.console)


def main():
    console = Console()
    console.print("[bold green]Hello![/bold green]")
    console.print("[bold blue]=== Japanese Vocabulary Learning Tool ===[/bold blue]")

    learner = VocabularyLearner()

    # Start with practice mode
    practice_mode(
        learner.vocabulary,
        learner.progress,
        learner.console,
        learner.japanese_converter,
        lambda word, success: update_progress(
            word, success, learner.progress, learner.save_progress
        ),
        lambda: show_help(learner.vim_commands, learner.console),
        lambda word_pair: show_word_statistics(word_pair, learner.progress, learner.console),
        learner.save_progress,
    )

    while True:
        console.print("\n[bold]Main Menu[/bold]")
        console.print("[purple]1.[/purple] Practice vocabulary")
        console.print("[purple]2.[/purple] Show progress")
        console.print("[purple]3.[/purple] Add vocabulary")
        console.print("[purple]4.[/purple] Reset progress")
        console.print("[blue]:q[/blue] Quit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            practice_mode(
                learner.vocabulary,
                learner.progress,
                learner.console,
                learner.japanese_converter,
                lambda word, success: update_progress(
                    word, success, learner.progress, learner.save_progress
                ),
                lambda: show_help(learner.vim_commands, learner.console),
                lambda word_pair: show_word_statistics(
                    word_pair, learner.progress, learner.console
                ),
                learner.save_progress,
            )
        elif choice == "2":
            show_progress(learner.vocabulary, learner.progress, learner.console)
            if not Confirm.ask("\nReturn to menu?"):
                break
        elif choice == "3":
            add_vocabulary(
                learner.vocab_file,
                learner.vocabulary,
                learner.vocab_ref,
                learner.console,
                lambda: load_vocabulary(learner.vocab_file, learner.vocab_ref, learner.console),
            )
        elif choice == "4":
            reset_progress(
                learner.progress_file,
                learner.progress_ref,
                learner.progress,
                learner.save_progress,
                learner.console,
            )
        elif choice == ":q":
            console.print("\n[yellow]Saving progress...[/yellow]")
            learner.save_progress()
            console.print("[green]Goodbye![/green]")
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting gracefully...")
        sys.exit(0)
