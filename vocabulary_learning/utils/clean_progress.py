"""Script to clean up progress data by removing non-word-ID entries and duplicates."""

import json
import os
import re
from datetime import datetime
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import auth, credentials, db
from rich.console import Console
from rich.panel import Panel


def clean_progress():
    """Clean up progress data by removing non-word-ID entries and duplicates."""
    console = Console()
    console.print(
        Panel.fit(
            "[bold blue]Progress Data Cleanup[/bold blue]\n\n"
            "This will:\n"
            "1. Remove entries that don't use word IDs\n"
            "2. Remove any duplicate entries\n"
            "3. Create a backup of the current progress file\n"
            "4. Save the cleaned data locally\n"
            "5. Push the cleaned data to Firebase",
            title="Progress Cleanup",
            border_style="blue",
        )
    )

    # Load environment variables
    load_dotenv()
    cred_path = os.path.expandvars(os.getenv("FIREBASE_CREDENTIALS_PATH"))

    # Load current progress data
    progress_path = Path("vocabulary_learning/data/progress.json")
    if not progress_path.exists():
        console.print("[red]Error: progress.json not found![/red]")
        return

    try:
        with open(progress_path, "r", encoding="utf-8") as f:
            progress = json.load(f)

        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = progress_path.parent / f"progress_backup_{timestamp}.json"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        console.print(f"[green]✓ Created backup at {backup_path}[/green]")

        # Count entries before cleanup
        total_before = len(progress)

        # Clean up progress data
        word_id_pattern = re.compile(r"^word_\d{6}$")

        # First, identify entries to remove (non-word-ID format)
        invalid_entries = [k for k in progress.keys() if not word_id_pattern.match(k)]

        # Remove invalid entries
        for key in invalid_entries:
            del progress[key]

        # Check for duplicates (same word ID with different casing)
        seen_ids = {}
        duplicates = []
        for word_id in list(progress.keys()):
            lower_id = word_id.lower()
            if lower_id in seen_ids:
                # Keep the entry with more attempts/progress
                old_attempts = seen_ids[lower_id]["attempts"]
                new_attempts = progress[word_id]["attempts"]
                if new_attempts > old_attempts:
                    # Remove the old entry with less attempts
                    old_id = next(
                        k for k in progress.keys() if k.lower() == lower_id and k != word_id
                    )
                    duplicates.append((old_id, word_id))
                    del progress[old_id]
                else:
                    # Remove the new entry
                    duplicates.append((word_id, seen_ids[lower_id]["id"]))
                    del progress[word_id]
            else:
                seen_ids[lower_id] = {"id": word_id, "attempts": progress[word_id]["attempts"]}

        # Report results
        if invalid_entries:
            console.print("\n[yellow]Removed invalid entries:[/yellow]")
            for entry in invalid_entries:
                console.print(f"[dim]- {entry}[/dim]")

        if duplicates:
            console.print("\n[yellow]Resolved duplicates:[/yellow]")
            for removed, kept in duplicates:
                console.print(f"[dim]- Removed {removed}, kept {kept}[/dim]")

        # Save cleaned data locally
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        console.print("\n[green]✓ Saved cleaned data locally[/green]")

        # Push to Firebase
        if not os.path.exists(cred_path):
            console.print(f"[red]Error: Firebase credentials not found at {cred_path}[/red]")
            return

        try:
            # Initialize Firebase
            try:
                app = firebase_admin.get_app()
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

            # Push to Firebase
            progress_ref = db.reference(f"/progress/{user_id}")
            progress_ref.set(progress)
            console.print("[green]✓ Pushed cleaned data to Firebase[/green]")

            console.print(
                Panel.fit(
                    "[bold green]Cleanup completed successfully![/bold green]\n"
                    f"✓ Removed {len(invalid_entries)} invalid entries\n"
                    f"✓ Resolved {len(duplicates)} duplicates\n"
                    f"✓ {len(progress)} valid entries remaining\n"
                    "✓ Backup created with timestamp\n"
                    "✓ Cleaned data saved locally\n"
                    "✓ Cleaned data pushed to Firebase",
                    title="✓ Success",
                    border_style="green",
                )
            )

        except Exception as e:
            console.print(f"[red]Error pushing to Firebase: {str(e)}[/red]")
            console.print(
                "[yellow]Data has been cleaned and saved locally, but could not be pushed to Firebase.[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]Error during cleanup: {str(e)}[/red]")


if __name__ == "__main__":
    clean_progress()
