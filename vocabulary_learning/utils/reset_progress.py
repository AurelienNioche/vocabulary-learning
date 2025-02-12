import json
import os
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import auth, credentials, db
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm


def reset_progress():
    console = Console()
    console.print(
        Panel.fit(
            "[bold red]WARNING: Progress Reset Tool[/bold red]\n\n"
            "This will:\n"
            "1. Delete your local progress file\n"
            "2. Reset your Firebase progress data\n"
            "3. Create a new empty progress file\n\n"
            "[bold red]This action cannot be undone![/bold red]",
            title="⚠️  Warning",
            border_style="red",
        )
    )

    # Double confirmation for safety
    if not Confirm.ask(
        "[bold red]Are you absolutely sure you want to reset all progress?[/bold red]"
    ):
        console.print("[yellow]Operation cancelled.[/yellow]")
        return

    if not Confirm.ask(
        "[bold red]This will delete ALL your learning progress. Type 'y' to confirm:[/bold red]"
    ):
        console.print("[yellow]Operation cancelled.[/yellow]")
        return

    # Load environment variables
    load_dotenv()
    cred_path = os.path.expandvars(os.getenv("FIREBASE_CREDENTIALS_PATH"))

    # Reset local progress file
    progress_path = Path("data/progress.json")
    if progress_path.exists():
        try:
            # Create backup before deleting
            backup_path = progress_path.with_suffix(".json.bak")
            progress_path.rename(backup_path)
            console.print("[green]✓ Created backup of current progress file[/green]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not create backup: {str(e)}[/yellow]")

        progress_path.unlink(missing_ok=True)
        console.print("[green]✓ Local progress file deleted[/green]")

    # Create empty progress file
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump({}, f)
    console.print("[green]✓ Created new empty progress file[/green]")

    # Reset Firebase progress
    if not os.path.exists(cred_path):
        console.print(f"[yellow]Warning: Firebase credentials not found at {cred_path}[/yellow]")
        console.print(
            "[yellow]Local progress has been reset, but Firebase could not be updated.[/yellow]"
        )
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
        password = os.getenv("FIREBASE_USER_PASSWORD")

        if not email or not password:
            console.print(
                "[yellow]Warning: Firebase user credentials not found in .env file[/yellow]"
            )
            console.print(
                "[yellow]Local progress has been reset, but Firebase could not be updated.[/yellow]"
            )
            return

        # Get user ID
        try:
            user = auth.get_user_by_email(email)
            user_id = user.uid
        except auth.UserNotFoundError:
            console.print(f"[yellow]Warning: User not found: {email}[/yellow]")
            console.print(
                "[yellow]Local progress has been reset, but Firebase could not be updated.[/yellow]"
            )
            return

        # Reset progress in Firebase
        progress_ref = db.reference(f"/progress/{user_id}")
        progress_ref.set({})
        console.print("[green]✓ Firebase progress reset[/green]")

        console.print(
            Panel.fit(
                "[bold green]Progress has been completely reset![/bold green]\n"
                "✓ Local progress file deleted and recreated\n"
                "✓ Backup created (.json.bak)\n"
                "✓ Firebase progress cleared\n\n"
                "You can now start fresh with your vocabulary practice.",
                title="✓ Success",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]Error during Firebase reset: {str(e)}[/red]")
        console.print(
            "[yellow]Local progress has been reset, but there was an error updating Firebase.[/yellow]"
        )


if __name__ == "__main__":
    reset_progress()
