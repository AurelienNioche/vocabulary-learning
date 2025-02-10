from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from datetime import datetime
from typing import Dict, Any, Tuple

class UIManager:
    def __init__(self):
        self.console = Console()
        self.vim_commands = {
            ':q': 'quit program',
            ':m': 'return to menu',
            ':h': 'show help',
            ':s': 'show word statistics',
            ':S': 'show all statistics',
            ':e': 'show example',
            ':d': 'show answer (don\'t know)'
        }

    def show_help(self) -> None:
        table = Table(title="Available Commands")
        table.add_column("Command", style="bold")
        table.add_column("Description", style="green")
        
        for cmd, desc in self.vim_commands.items():
            table.add_row(cmd, desc)
            
        self.console.print(table)

    def show_word_statistics(self, word_data: Dict[str, Any], progress: Dict[str, Any]) -> None:
        table = Table(title=f"Statistics for {word_data['hiragana']}")
        table.add_column("Information", style="bold")
        table.add_column("Value", style="green")

        stats = progress.get(word_data['hiragana'], {
            'attempts': 0,
            'successes': 0,
            'last_seen': 'Never'
        })

        # Add statistics to table
        success_rate = (stats['successes'] / stats['attempts'] * 100) if stats['attempts'] > 0 else 0
        table.add_row("Success Rate", f"{success_rate:.1f}%")
        table.add_row("Total Attempts", str(stats['attempts']))
        # Add more statistics as needed

        self.console.print(table)

    def check_answer(self, user_answer: str, correct_answer: str) -> Tuple[bool, str]:
        """Check if the answer is correct, handling multiple answers and typos."""
        # Implementation of answer checking logic
        pass
