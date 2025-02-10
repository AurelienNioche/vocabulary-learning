from pathlib import Path
from typing import Dict
import os
from dotenv import load_dotenv

class Config:
    """Configuration management for the vocabulary learner."""
    
    def __init__(self) -> None:
        load_dotenv()
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.vocab_file = self.data_dir / "vocabulary.json"
        self.progress_file = self.data_dir / "progress.json"
        
        self.firebase_config = self._load_firebase_config()
        
    def _load_firebase_config(self) -> Dict[str, str]:
        return {
            'credentials_path': os.getenv('FIREBASE_CREDENTIALS_PATH', ''),
            'database_url': os.getenv('FIREBASE_DATABASE_URL', ''),
            'user_email': os.getenv('FIREBASE_USER_EMAIL', ''),
            'user_password': os.getenv('FIREBASE_USER_PASSWORD', '')
        }
