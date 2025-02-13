import json
import os
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import auth, credentials, db
from rich.console import Console
from rich.prompt import Confirm


def sync_to_firebase():
    console = Console()
    console.print("\n[bold blue]=== Starting Firebase Sync ===[/bold blue]")

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
            console.print("[dim]Initializing new Firebase connection...[/dim]")
            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(
                cred, {"databaseURL": os.getenv("FIREBASE_DATABASE_URL")}
            )

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

        # Read local files
        files_to_sync = {
            "vocabulary": {"path": "vocabulary_learning/data/vocabulary.json", "ref": vocab_ref},
            "progress": {"path": "vocabulary_learning/data/progress.json", "ref": progress_ref},
        }

        for data_type, config in files_to_sync.items():
            json_path = Path(config["path"])
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

            if local_count != uploaded_count:
                console.print(
                    f"[yellow]Warning: {data_type} count mismatch. Local: {local_count}, Firebase: {uploaded_count}[/yellow]"
                )
                console.print("[yellow]Please verify your data and try again if needed.[/yellow]")
            else:
                console.print(
                    f"[green]✓ Successfully synced {local_count} {data_type} entries to Firebase![/green]"
                )
                console.print(f"[dim]Your {data_type} is now backed up in the cloud.[/dim]")

    except Exception as e:
        console.print(f"[red]Error during Firebase sync: {str(e)}[/red]")
        console.print("[yellow]Please check your Firebase configuration and try again.[/yellow]")


if __name__ == "__main__":
    sync_to_firebase()
