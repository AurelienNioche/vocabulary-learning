from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
import random
from vocab_learner.config import Config
from vocab_learner.vocabulary_manager import VocabularyManager
from vocab_learner.progress_manager import ProgressManager

class VocabularyLearner:
    def __init__(self, config: Config):
        self.config = config
        self.console = Console()
        
        # Initialize managers
        self.vocabulary_manager = VocabularyManager(
            vocab_file=config.vocab_file,
            firebase_ref=config.firebase_credentials
        )
        
        self.progress_manager = ProgressManager(
            progress_file=config.progress_file,
            firebase_ref=config.firebase_credentials
        )
        
        # Cross-reference between managers
        self.vocabulary_manager.progress_manager = self.progress_manager
        self.progress_manager.vocabulary = self.vocabulary_manager.vocabulary

    def show_menu(self):
        menu_text = Text()
        menu_text.append("\n1. ", style="bold cyan")
        menu_text.append("Practice vocabulary\n")
        menu_text.append("2. ", style="bold cyan")
        menu_text.append("Show progress\n")
        menu_text.append("3. ", style="bold cyan")
        menu_text.append("Add vocabulary\n")
        menu_text.append("q. ", style="bold red")
        menu_text.append("Quit")
        
        return Panel(
            menu_text,
            title="[bold blue]Japanese Vocabulary Learner[/bold blue]",
            border_style="blue"
        )

    def run(self):
        while True:
            self.console.clear()
            self.console.print(self.show_menu())
            
            choice = Prompt.ask(
                "\nWhat would you like to do?",
                choices=["1", "2", "3", "q"],
                default="1"
            )
            
            if choice == "1":
                self.practice_vocabulary()
            elif choice == "2":
                self.show_progress()
            elif choice == "3":
                self.add_vocabulary()
            elif choice == "q":
                self.console.print("[blue]Goodbye![/blue]")
                break

            if choice != "q":
                input("\nPress Enter to continue...")

    def practice_vocabulary(self):
        if self.vocabulary_manager.vocabulary.empty:
            self.console.print("[yellow]No vocabulary available. Please add some words first.[/yellow]")
            return

        while True:
            # Select a word based on priority
            word_idx = self._select_word()
            if word_idx is None:
                self.console.print("[green]You've completed all words for now![/green]")
                break

            word = self.vocabulary_manager.vocabulary.iloc[word_idx]
            
            self.console.print(f"\n[bold]Translate to French:[/bold] {word['hiragana']}")
            if word['kanji']:
                self.console.print(f"[dim](Kanji: {word['kanji']})[/dim]")

            answer = Prompt.ask("Your answer (:q to quit)")
            if answer.lower() == ":q":
                break

            correct = self._check_answer(answer, word['french'])
            self._update_progress(word_idx, correct)

    def _select_word(self):
        words = []
        priorities = []

        for idx, row in self.vocabulary_manager.vocabulary.iterrows():
            word_data = self.progress_manager.progress.get(str(idx))
            priority = self.progress_manager.calculate_priority(str(idx), word_data)
            if priority > 0:
                words.append(idx)
                priorities.append(priority)

        if not words:
            return None

        # Normalize priorities
        total = sum(priorities)
        if total > 0:
            priorities = [p/total for p in priorities]
            return random.choices(words, weights=priorities, k=1)[0]
        return random.choice(words)

    def _check_answer(self, given: str, correct: str) -> bool:
        given = given.lower().strip()
        correct_answers = [ans.lower().strip() for ans in correct.split("/")]
        
        if given in correct_answers:
            self.console.print("[green]Correct![/green]")
            return True
        else:
            self.console.print(f"[red]Incorrect. The answer was: {correct}[/red]")
            return False

    def _update_progress(self, word_idx: int, correct: bool):
        word_id = str(word_idx)
        if word_id not in self.progress_manager.progress:
            self.progress_manager.progress[word_id] = {"attempts": 0, "successes": 0}
        
        self.progress_manager.progress[word_id]["attempts"] += 1
        if correct:
            self.progress_manager.progress[word_id]["successes"] += 1
        
        self.progress_manager.save_progress()

    def show_progress(self):
        if not self.progress_manager.progress:
            self.console.print("[yellow]No progress data available yet.[/yellow]")
            return

        self.console.print("\n[bold]Progress Report:[/bold]")
        for word_id, data in self.progress_manager.progress.items():
            word = self.vocabulary_manager.vocabulary.iloc[int(word_id)]
            success_rate = (data['successes'] / data['attempts'] * 100) if data['attempts'] > 0 else 0
            self.console.print(
                f"{word['hiragana']}: {success_rate:.1f}% "
                f"({data['successes']}/{data['attempts']} correct)"
            )

    def add_vocabulary(self):
        hiragana = Prompt.ask("Enter hiragana")
        kanji = Prompt.ask("Enter kanji (optional)", default="")
        french = Prompt.ask("Enter French translation(s) (separate multiple with /)")
        
        new_word = {
            'hiragana': hiragana,
            'kanji': kanji,
            'french': french,
            'example_sentence': ""
        }
        
        self.vocabulary_manager.vocabulary = self.vocabulary_manager.vocabulary.append(
            new_word,
            ignore_index=True
        )
        self.vocabulary_manager.save_vocabulary()
        self.console.print("[green]Word added successfully![/green]")
