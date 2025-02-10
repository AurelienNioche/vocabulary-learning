from vocab_learner.config import Config
from vocab_learner.firebase_manager import FirebaseManager
from vocab_learner.japanese_utils import JapaneseTextConverter
from vocab_learner.vocabulary_manager import VocabularyManager
from vocab_learner.progress_manager import ProgressManager
from vocab_learner.ui_manager import UIManager
from vocab_learner.logger import setup_logger

class VocabularyLearner:
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger('vocab_learner')
        self.ui = UIManager()
        
        # Initialize Firebase if configured
        self.firebase = None
        if self.config.firebase_config['credentials_path']:
            self.firebase = FirebaseManager(
                self.config.firebase_config['credentials_path'],
                self.config.firebase_config['database_url']
            )
        
        # Initialize managers
        self.vocab_manager = VocabularyManager(
            self.config.vocab_file,
            self.firebase.vocab_ref if self.firebase else None
        )
        self.progress_manager = ProgressManager(
            self.config.progress_file,
            self.firebase.progress_ref if self.firebase else None
        )
        self.japanese = JapaneseTextConverter()

    def practice(self):
        """Main practice loop."""
        # Implementation of practice logic using the managers
        pass

def main():
    learner = VocabularyLearner()
    learner.practice()

if __name__ == "__main__":
    main()