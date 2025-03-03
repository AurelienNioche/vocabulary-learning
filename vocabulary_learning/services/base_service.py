"""Base service class for handling data paths."""

import os
import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console

from vocabulary_learning.core.constants import ENV_FILE
from vocabulary_learning.core.paths import get_data_dir


class BaseService:
    def __init__(self, console: Optional[Console] = None):
        """Initialize base service.

        Args:
            console: Rich console for output (optional)
        """
        self.console = console or Console()
        self.data_dir = Path(get_data_dir())

        # Create necessary directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "data").mkdir(exist_ok=True)
        (self.data_dir / "firebase").mkdir(exist_ok=True)

    def get_data_file(self, filename: str) -> Path:
        """Get path to a data file.

        If the file doesn't exist and there's a default version,
        copy the default file to the user's data directory.

        Args:
            filename: Name of the file

        Returns:
            Path to the file in the data directory
        """
        user_file = self.data_dir / "data" / filename
        if not user_file.exists():
            # Check for default data
            package_dir = Path(__file__).parent.parent
            default_file = package_dir / "default_data" / filename
            if default_file.exists():
                self.console.print(f"[dim]Copying default {filename} to user directory...[/dim]")
                shutil.copy2(default_file, user_file)
            else:
                self.console.print(f"[yellow]Warning: No default {filename} found[/yellow]")
                # Create empty file
                user_file.write_text("{}")
        return user_file

    def get_firebase_file(self, filename: str) -> Path:
        """Get path to a Firebase file.

        Args:
            filename: Name of the file

        Returns:
            Path to the file in the firebase directory
        """
        return self.data_dir / "firebase" / filename

    def get_env_file(self) -> Path:
        """Get path to the .env file.

        Returns:
            Path to the .env file
        """
        return self.data_dir / ENV_FILE
