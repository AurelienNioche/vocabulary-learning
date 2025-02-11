from vocab_learner.vocab_learner import VocabularyLearner
from vocab_learner.config import Config

def main():
    config = Config.load()
    learner = VocabularyLearner(config)
    learner.run()

if __name__ == "__main__":
    main()
