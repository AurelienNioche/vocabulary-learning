"""Script to migrate data to OS-specific locations."""

import json
import os
import shutil
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from vocabulary_learning.core.utils import get_data_dir


def migrate_data():
    """Migrate data from old location to new OS-specific location."""
    console = Console()
    console.print(
        Panel.fit(
            "[bold blue]Data Migration Tool[/bold blue]\n\n"
            "This will:\n"
            "1. Move your data to the OS-specific location\n"
            "2. Create backups of existing files\n"
            "3. Update Firebase configuration",
            title="Data Migration",
            border_style="blue",
        )
    )

    # Get paths
    old_data_dir = Path("vocabulary_learning/data")
    old_firebase_dir = Path(".firebase")
    old_env_file = Path(".env")

    new_base_dir = Path(get_data_dir())
    new_data_dir = new_base_dir / "data"
    new_firebase_dir = new_base_dir / "firebase"

    # Create new directories
    new_data_dir.mkdir(parents=True, exist_ok=True)
    new_firebase_dir.mkdir(parents=True, exist_ok=True)

    # Function to safely copy files
    def safe_copy(src: Path, dst: Path, file_type: str):
        if src.exists():
            if dst.exists():
                # Create backup
                backup = dst.with_suffix(f"{dst.suffix}.bak")
                shutil.copy2(dst, backup)
                console.print(f"[dim]Created backup of existing {file_type} at {backup}[/dim]")

            # Copy file
            shutil.copy2(src, dst)
            console.print(f"[green]✓ Copied {file_type} to {dst}[/green]")
            return True
        return False

    # Migrate vocabulary and progress
    files_migrated = False
    if old_data_dir.exists():
        for file in old_data_dir.glob("*.json"):
            dst = new_data_dir / file.name
            if safe_copy(file, dst, f"{file.stem} data"):
                files_migrated = True

    # Migrate Firebase credentials
    if old_firebase_dir.exists():
        creds_file = old_firebase_dir / "credentials.json"
        if safe_copy(creds_file, new_firebase_dir / "credentials.json", "Firebase credentials"):
            files_migrated = True

    # Migrate .env file
    if old_env_file.exists():
        # Read existing .env
        with open(old_env_file, "r") as f:
            env_content = f.read()

        # Update Firebase credentials path
        env_content = env_content.replace(
            "/app/.firebase/credentials.json", "/app/firebase/credentials.json"
        )

        # Write to new location
        new_env = new_base_dir / ".env"
        if new_env.exists():
            backup = new_env.with_suffix(".env.bak")
            shutil.copy2(new_env, backup)
            console.print(f"[dim]Created backup of existing .env at {backup}[/dim]")

        with open(new_env, "w") as f:
            f.write(env_content)
        console.print(f"[green]✓ Migrated .env file to {new_env}[/green]")
        files_migrated = True

    if files_migrated:
        console.print(
            Panel.fit(
                "[bold green]Migration completed successfully![/bold green]\n"
                f"Your data has been moved to: {new_base_dir}\n\n"
                "The following locations are now used:\n"
                f"- Vocabulary and progress: {new_data_dir}\n"
                f"- Firebase credentials: {new_firebase_dir}\n"
                f"- Environment config: {new_base_dir / '.env'}\n\n"
                "You can now safely remove the old files if you wish.",
                title="✓ Success",
                border_style="green",
            )
        )

        if Confirm.ask("Would you like to remove the old files?"):
            try:
                if old_data_dir.exists():
                    shutil.rmtree(old_data_dir.parent)
                    console.print("[green]✓ Removed old data directory[/green]")
                if old_firebase_dir.exists():
                    shutil.rmtree(old_firebase_dir)
                    console.print("[green]✓ Removed old Firebase directory[/green]")
                if old_env_file.exists():
                    old_env_file.unlink()
                    console.print("[green]✓ Removed old .env file[/green]")
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not remove some old files: {str(e)}[/yellow]"
                )
    else:
        console.print("[yellow]No files found to migrate.[/yellow]")


if __name__ == "__main__":
    migrate_data()
