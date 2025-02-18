"""Script to sync local data with Firebase."""

import json
import os
import sys
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import auth, credentials, db
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()


def get_data_dir() -> str:
    """Get the OS-specific data directory for storing application data."""
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/VocabularyLearning")
    else:
        return os.path.expanduser("~/.local/share/vocabulary-learning")


def sync_to_firebase():
    """Sync local data with Firebase."""
    console.print("\n=== Starting Firebase Sync ===")

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
        try:
            app = firebase_admin.get_app()
            console.print("[dim]Using existing Firebase connection[/dim]")
        except ValueError:
            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(
                cred, {"databaseURL": os.getenv("FIREBASE_DATABASE_URL")}
            )

        # Get user credentials
        email = os.getenv("FIREBASE_USER_EMAIL")
        if not email:
            raise ValueError("Firebase user email not found in .env")

        # Get user ID
        user = auth.get_user_by_email(email)
        user_id = user.uid
        console.print(f"[dim]Authenticated as: {email}[/dim]")

        # Set up database references
        vocab_ref = db.reference(f"/vocabulary/{user_id}")
        progress_ref = db.reference(f"/progress/{user_id}")

        # Get data directory
        data_dir = Path(get_data_dir()) / "data"

        # Read local files
        files_to_sync = {
            "vocabulary": {"path": data_dir / "vocabulary.json", "ref": vocab_ref},
            "progress": {"path": data_dir / "progress.json", "ref": progress_ref},
        }

        for data_type, config in files_to_sync.items():
            json_path = config["path"]
            if not json_path.exists():
                console.print(f"[red]Error: {json_path} not found[/red]")
                console.print(
                    f"[yellow]Please make sure you have a {data_type} file in the data directory.[/yellow]"
                )
                continue

            with open(json_path, "r", encoding="utf-8") as f:
                local_data = json.load(f)

            # Confirm sync if there's existing data
            existing_data = config["ref"].get()
            if existing_data:
                if not Confirm.ask(
                    f"[yellow]Existing {data_type} data found in Firebase. Do you want to overwrite it?[/yellow]"
                ):
                    console.print(f"[yellow]{data_type.capitalize()} sync cancelled.[/yellow]")
                    continue

            # Upload to Firebase
            console.print(f"[dim]Uploading {data_type} to Firebase...[/dim]")
            config["ref"].set(local_data)

            # Verify upload
            uploaded_data = config["ref"].get()
            if not uploaded_data:
                raise Exception(f"Failed to verify uploaded {data_type} data")

            # Compare counts
            local_count = len(local_data)
            uploaded_count = len(uploaded_data)
            if local_count == uploaded_count:
                console.print(
                    f"[green]✓ Successfully synced {local_count} {data_type} items[/green]"
                )
            else:
                console.print(
                    f"[yellow]Warning: Local {data_type} count ({local_count}) differs from uploaded count ({uploaded_count})[/yellow]"
                )

    except Exception as e:
        console.print(f"[red]Error during sync: {str(e)}[/red]")


if __name__ == "__main__":
    sync_to_firebase()
