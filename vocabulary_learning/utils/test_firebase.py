"""Test Firebase connection and functionality."""

import json
import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, db
from rich.console import Console
from rich.table import Table

console = Console()


def test_firebase_connection():
    """Test Firebase connection and display data."""
    load_dotenv()

    cred_path = os.path.expandvars(os.getenv("FIREBASE_CREDENTIALS_PATH"))

    if not os.path.exists(cred_path):
        console.print(
            f"[red]Error: Firebase credentials not found at {cred_path}[/red]"
        )
        return

    try:
        # Initialize Firebase
        try:
            firebase_admin.get_app()
            console.print("[dim]Using existing Firebase connection[/dim]")
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
        user_id = "test_user"  # For testing purposes
        console.print(f"[dim]Using test user ID: {user_id}[/dim]")

        # Get references
        progress_ref = db.reference(f"/progress/{user_id}")
        vocab_ref = db.reference(f"/vocabulary/{user_id}")

        # Get data
        progress_data = progress_ref.get() or {}
        vocab_data = vocab_ref.get() or {}

        # Display data
        console.print("\n[bold]Progress Data:[/bold]")
        console.print_json(json.dumps(progress_data, indent=2, ensure_ascii=False))

        # Display vocabulary
        table = Table(title="Vocabulary")
        table.add_column("ID", style="cyan")
        table.add_column("Hiragana", style="magenta")
        table.add_column("Kanji", style="green")
        table.add_column("French", style="yellow")

        for word_id, word_data in vocab_data.items():
            table.add_row(
                word_id,
                word_data["hiragana"],
                word_data["kanji"],
                word_data["french"],
            )

        console.print(table)

        # Display progress statistics
        table = Table(title="Progress Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        total_words = len(vocab_data)
        words_started = len(progress_data)
        words_mastered = sum(
            1 for data in progress_data.values() if data["successes"] >= 5
        )

        table.add_row("Total Words", str(total_words))
        table.add_row("Words Started", str(words_started))
        table.add_row("Words Mastered", str(words_mastered))

        console.print(table)

        console.print("[green]✓ Firebase connection test successful![/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


if __name__ == "__main__":
    test_firebase_connection()
