"""Script to fix progress data by converting Japanese word keys to proper numeric IDs."""

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel


def fix_progress():
    """Fix progress data by converting Japanese word keys to proper numeric IDs."""
    console = Console()
    console.print(
        Panel.fit(
            "[bold blue]Progress Data Fix[/bold blue]\n\n"
            "This will:\n"
            "1. Create a backup of the current progress file\n"
            "2. Convert any Japanese word keys to proper numeric IDs\n"
            "3. Save the fixed data locally\n"
            "4. Push the fixed data to Firebase",
            title="Progress Fix",
            border_style="blue",
        )
    )

    # Get data directory
    data_dir = Path(os.path.expanduser("~/Library/Application Support/VocabularyLearning/data"))
    if not data_dir.exists():
        console.print(f"[red]Data directory not found at {data_dir}[/red]")
        return

    # Load current progress data
    progress_path = data_dir / "progress.json"
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
        console.print(f"[dim]Total entries before fix: {total_before}[/dim]")

        # Find the highest numeric ID
        max_id = 0
        for key in progress.keys():
            if key.isdigit():
                max_id = max(max_id, int(key))

        # Fix progress data
        fixed_progress = {}
        japanese_entries = []

        for key, data in progress.items():
            if key.isdigit():
                # Already in correct format
                fixed_progress[key] = data
            else:
                # Japanese word key - assign next available ID
                max_id += 1
                new_key = str(max_id).zfill(6)
                fixed_progress[new_key] = data
                japanese_entries.append((key, new_key))

        # Save fixed data
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(fixed_progress, f, ensure_ascii=False, indent=2)

        # Report changes
        if japanese_entries:
            console.print("\n[yellow]Converted entries:[/yellow]")
            for old_key, new_key in japanese_entries:
                console.print(f"[dim]- {old_key} → {new_key}[/dim]")

        console.print(
            f"\n[green]✓ Fixed progress data saved ({len(fixed_progress)} entries)[/green]"
        )

        # Try to update Firebase
        try:
            from vocabulary_learning.core.firebase_config import initialize_firebase

            load_dotenv()
            progress_ref, _ = initialize_firebase(
                console=console,
                env_file=str(
                    Path(
                        os.path.expanduser("~/Library/Application Support/VocabularyLearning/.env")
                    )
                ),
            )

            if progress_ref:
                console.print("[dim]Updating Firebase...[/dim]", end="")
                progress_ref.set(fixed_progress)
                console.print("[green] ✓[/green]")
            else:
                console.print("[yellow]Could not initialize Firebase connection[/yellow]")
                console.print("[yellow]Changes saved locally only[/yellow]")

        except Exception as e:
            console.print(f"[yellow]Failed to update Firebase: {str(e)}[/yellow]")
            console.print("[yellow]Changes saved locally only[/yellow]")

    except Exception as e:
        console.print(f"[red]Error fixing progress data: {str(e)}[/red]")
        return


if __name__ == "__main__":
    fix_progress()
