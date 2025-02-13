"""Firebase loading utilities."""

import json
import os
import sys
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import auth, credentials, db
from rich.console import Console
from rich.panel import Panel

console = Console()


def initialize_firebase():
    """Initialize Firebase connection."""
    cred_path = os.path.expandvars(os.getenv("FIREBASE_CREDENTIALS_PATH"))

    if not os.path.exists(cred_path):
        console.print(f"[red]Error: Firebase credentials not found at {cred_path}[/red]")
        sys.exit(1)

    try:
        try:
            app = firebase_admin.get_app()
            console.print("[dim]Using existing Firebase connection[/dim]")
        except ValueError:
            console.print("[dim]Initializing new Firebase connection...[/dim]")
            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(
                cred, {"databaseURL": os.getenv("FIREBASE_DATABASE_URL")}
            )
            console.print("[green]Firebase initialized successfully![/green]")
        return app
    except Exception as e:
        console.print(f"[red]Failed to initialize Firebase: {str(e)}[/red]")
        sys.exit(1)


def load_from_firebase():
    console.print("\n[bold blue]=== Loading Data from Firebase ===[/bold blue]")

    # Load environment variables
    load_dotenv()
    cred_path = os.path.expandvars(os.getenv("FIREBASE_CREDENTIALS_PATH"))

    if not os.path.exists(cred_path):
        console.print(f"[red]Error: Firebase credentials not found at {cred_path}[/red]")
        console.print(
            "[yellow]Please make sure you have set up Firebase credentials correctly.[/yellow]"
        )
        return

    try:
        # Initialize Firebase
        app = initialize_firebase()

        # Get user credentials
        email = os.getenv("FIREBASE_USER_EMAIL")
        password = os.getenv("FIREBASE_USER_PASSWORD")

        if not email or not password:
            console.print("[red]Error: Firebase user credentials not found in .env file[/red]")
            console.print(
                "[yellow]Please set FIREBASE_USER_EMAIL and FIREBASE_USER_PASSWORD in your .env file[/yellow]"
            )
            return

        # Get user ID
        try:
            user = auth.get_user_by_email(email)
            user_id = user.uid
            console.print(f"[dim]Authenticated as: {email}[/dim]")
        except auth.UserNotFoundError:
            console.print(f"[red]Error: User not found: {email}[/red]")
            return

        # Set up database references
        vocab_ref = db.reference(f"/vocabulary/{user_id}")
        progress_ref = db.reference(f"/progress/{user_id}")

        # Create data directory if it doesn't exist
        data_dir = Path("vocabulary_learning/data")
        data_dir.mkdir(exist_ok=True)

        # Load vocabulary data
        console.print("\n[dim]Loading vocabulary data...[/dim]")
        vocab_data = vocab_ref.get()

        if vocab_data:
            # Save Firebase vocabulary locally
            vocab_path = data_dir / "vocabulary.json"
            with open(vocab_path, "w", encoding="utf-8") as f:
                json.dump(vocab_data, f, ensure_ascii=False, indent=2)
            console.print(f"[green]✓ Loaded {len(vocab_data)} words from Firebase[/green]")
        else:
            console.print("[yellow]No vocabulary data found in Firebase[/yellow]")

        # Load progress data
        console.print("\n[dim]Loading progress data...[/dim]")
        progress_data = progress_ref.get()

        if progress_data:
            # Save Firebase progress locally
            progress_path = data_dir / "progress.json"
            with open(progress_path, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            console.print(f"[green]✓ Loaded progress data for {len(progress_data)} words[/green]")
        else:
            # Create empty progress file if none exists
            progress_path = data_dir / "progress.json"
            if not progress_path.exists():
                with open(progress_path, "w", encoding="utf-8") as f:
                    json.dump({}, f)
            console.print("[yellow]No progress data found in Firebase[/yellow]")

        if vocab_data or progress_data:
            console.print(
                Panel.fit(
                    "[bold green]Successfully loaded data from Firebase![/bold green]\n"
                    + (f"✓ Loaded {len(vocab_data)} vocabulary words\n" if vocab_data else "")
                    + (
                        f"✓ Loaded progress for {len(progress_data)} words"
                        if progress_data
                        else "✓ Created empty progress file"
                    ),
                    title="✓ Success",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel.fit(
                    "[yellow]No data found in Firebase[/yellow]\n"
                    "You may need to:\n"
                    "1. Upload your vocabulary first, or\n"
                    "2. Start fresh with new vocabulary",
                    title="⚠️ Note",
                    border_style="yellow",
                )
            )

    except Exception as e:
        console.print(f"[red]Error loading from Firebase: {str(e)}[/red]")
        console.print("[yellow]Please check your Firebase configuration and try again.[/yellow]")


if __name__ == "__main__":
    load_from_firebase()
