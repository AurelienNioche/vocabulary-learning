"""Utilities for managing application paths and directories."""

import sys
from pathlib import Path

from vocabulary_learning.core.constants import (
    LINUX_DATA_DIR,
    MACOS_DATA_DIR,
    PROGRESS_FILE,
    VOCABULARY_FILE,
)


def get_data_dir() -> str:
    """Get the OS-specific data directory for storing application data.

    Returns
    -------
        Path to the data directory
    """
    if sys.platform == "darwin":
        return str(MACOS_DATA_DIR)
    else:
        return str(LINUX_DATA_DIR)


def get_progress_file_path() -> Path:
    """Get the path to the progress.json file.

    Returns
    -------
        Path object pointing to the progress.json file
    """
    return Path(get_data_dir()) / "data" / PROGRESS_FILE


def get_vocabulary_file_path() -> Path:
    """Get the path to the vocabulary.json file.

    Returns
    -------
        Path object pointing to the vocabulary.json file
    """
    return Path(get_data_dir()) / "data" / VOCABULARY_FILE
