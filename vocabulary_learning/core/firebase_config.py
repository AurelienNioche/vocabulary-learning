"""Firebase configuration and initialization."""

import json
import os
from pathlib import Path

import firebase_admin
import httpx
from dotenv import load_dotenv
from firebase_admin import auth, credentials, db
from rich.console import Console

from vocabulary_learning.core.ssl_config import create_ssl_context


def initialize_firebase(console: Console, env_file: str = None):
    """Initialize Firebase connection and return database references."""
    # Load environment variables if not already loaded
    if env_file and Path(env_file).exists():
        load_dotenv(env_file)
    else:
        console.print(f"Error: Environment file not found at {env_file}")
        return None, None

    # Get Firebase configuration from environment variables
    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    database_url = os.getenv("FIREBASE_DATABASE_URL")
    user_email = os.getenv("FIREBASE_USER_EMAIL")

    if not all([creds_path, database_url, user_email]):
        console.print("Error: Missing required Firebase configuration")
        return None, None

    try:
        # Initialize Firebase Admin SDK if not already initialized
        if not firebase_admin._apps:
            # Configure SSL context for secure connections
            ssl_context = create_ssl_context()
            httpx.Client(verify=ssl_context)

            # Initialize Firebase with credentials
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred, {"databaseURL": database_url})

        # Authenticate user
        user = auth.get_user_by_email(user_email)
        console.print("Firebase initialized successfully!")
        console.print(f"Authenticated as: {user.email}")

        # Get database references
        progress_ref = db.reference("progress")
        vocab_ref = db.reference("vocabulary")

        return progress_ref, vocab_ref

    except Exception as e:
        console.print(f"[red]Error initializing Firebase: {str(e)}[/red]")
        return None, None
