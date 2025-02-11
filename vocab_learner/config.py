import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

@dataclass
class Config:
    vocab_file: str
    progress_file: str
    firebase_credentials: dict | None = None
    
    @classmethod
    def load(cls):
        load_dotenv()
        
        # Set default paths
        data_dir = Path.home() / ".vocab-learner"
        data_dir.mkdir(exist_ok=True)
        
        vocab_file = data_dir / "vocabulary.json"
        progress_file = data_dir / "progress.json"
        
        # Load Firebase credentials if available
        firebase_creds = None
        if os.getenv("FIREBASE_CREDENTIALS"):
            firebase_creds = os.getenv("FIREBASE_CREDENTIALS")
            
        return cls(
            vocab_file=str(vocab_file),
            progress_file=str(progress_file),
            firebase_credentials=firebase_creds
        )
