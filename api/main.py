"""FastAPI backend for vocabulary learning application."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import firebase_admin
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import auth, credentials, db
from pydantic import BaseModel

from vocabulary_learning.services.practice_service import PracticeService
from vocabulary_learning.services.progress_service import ProgressService
from vocabulary_learning.services.vocabulary_service import VocabularyService

app = FastAPI(title="Vocabulary Learning API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create data directory if it doesn't exist
data_dir = Path("data")
data_dir.mkdir(parents=True, exist_ok=True)

# Initialize Firebase
load_dotenv()
cred_path = os.path.expandvars(os.getenv("FIREBASE_CREDENTIALS_PATH"))

if not os.path.exists(cred_path):
    raise Exception(f"Firebase credentials not found at {cred_path}")

try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(
        cred, {"databaseURL": os.getenv("FIREBASE_DATABASE_URL")}
    )

# Get user credentials
email = os.getenv("FIREBASE_USER_EMAIL")
if not email:
    raise ValueError("Firebase user email not found in .env")

# Get user ID
user = auth.get_user_by_email(email)
user_id = user.uid

# Set up database references
vocab_ref = db.reference(f"/vocabulary/{user_id}")
progress_ref = db.reference(f"/progress/{user_id}")

# Initialize services with absolute paths
vocabulary_service = VocabularyService(str(data_dir / "vocabulary.json"), vocab_ref)
progress_service = ProgressService(str(data_dir / "progress.json"), progress_ref)
practice_service = PracticeService(vocabulary_service, progress_service)

# Load initial data from Firebase
try:
    # Load vocabulary
    vocab_data = vocab_ref.get() or {}
    with open(data_dir / "vocabulary.json", "w", encoding="utf-8") as f:
        json.dump(vocab_data, f, ensure_ascii=False, indent=2)

    # Load progress
    progress_data = progress_ref.get() or {}
    with open(data_dir / "progress.json", "w", encoding="utf-8") as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)
except Exception as e:
    print(f"Warning: Failed to load initial data from Firebase: {e}")


# Models
class WordEntry(BaseModel):
    """Model for adding/updating vocabulary entries."""

    word: str
    translations: List[str]
    example_sentences: Optional[List[Tuple[str, str]]] = None


class PracticeResult(BaseModel):
    """Model for submitting practice results."""

    word: str
    success: bool


# Vocabulary endpoints
@app.get("/vocabulary", response_model=List[str])
async def get_vocabulary():
    """Get list of all vocabulary words."""
    return vocabulary_service.get_all_words()


@app.get("/vocabulary/{word}", response_model=Dict)
async def get_word(word: str):
    """Get details for a specific word."""
    word_details = practice_service.get_word_details(word)
    if not word_details:
        raise HTTPException(status_code=404, detail="Word not found")
    return word_details


@app.post("/vocabulary")
async def add_word(word_entry: WordEntry):
    """Add a new word to vocabulary."""
    success = vocabulary_service.add_word(
        word_entry.word,
        word_entry.translations,
        word_entry.example_sentences or [],
    )
    if not success:
        raise HTTPException(status_code=400, detail="Invalid word entry")
    return {"status": "success"}


@app.put("/vocabulary/{word}")
async def update_word(word: str, word_entry: WordEntry):
    """Update an existing word."""
    if word != word_entry.word:
        raise HTTPException(status_code=400, detail="Word mismatch in path and body")

    success = vocabulary_service.update_word(
        word,
        word_entry.translations,
        word_entry.example_sentences,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Word not found")
    return {"status": "success"}


@app.delete("/vocabulary/{word}")
async def delete_word(word: str):
    """Delete a word from vocabulary."""
    success = vocabulary_service.delete_word(word)
    if not success:
        raise HTTPException(status_code=404, detail="Word not found")
    return {"status": "success"}


@app.get("/vocabulary/search/{query}", response_model=List[str])
async def search_vocabulary(query: str):
    """Search vocabulary for words matching query."""
    return vocabulary_service.search_words(query)


# Practice endpoints
@app.get("/practice/words", response_model=List[str])
async def get_practice_words(num_words: int = 10):
    """Get words for practice session."""
    return practice_service.select_practice_words(num_words)


@app.post("/practice/result")
async def submit_practice_result(result: PracticeResult):
    """Submit result for a practice attempt."""
    practice_service.update_word_progress(result.word, result.success)
    return {"status": "success"}


@app.get("/practice/stats")
async def get_practice_stats():
    """Get overall practice statistics."""
    return practice_service.get_practice_stats()


@app.get("/practice/suggestions/{word}", response_model=List[Tuple[str, float]])
async def get_word_suggestions(word: str, num_suggestions: int = 3):
    """Get similar words as suggestions."""
    return practice_service.get_word_suggestions(word, num_suggestions)
