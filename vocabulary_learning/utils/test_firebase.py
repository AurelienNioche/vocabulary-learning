import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db, auth
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich import print_json
import json

def initialize_firebase():
    """Initialize Firebase connection."""
    load_dotenv()
    cred_path = os.path.expandvars(os.getenv('FIREBASE_CREDENTIALS_PATH'))
    
    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Credentials file not found at {cred_path}")
    
    try:
        app = firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(cred_path)
        app = firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
        })
    
    return app

def view_data(path=None):
    """View data from Firebase in a nicely formatted way."""
    console = Console()
    
    try:
        # Initialize Firebase if not already initialized
        initialize_firebase()
        
        # Get reference to the specified path or root
        ref = db.reference(path) if path else db.reference('/')
        
        # Get the data
        data = ref.get()
        
        if not data:
            console.print("[yellow]No data found.[/yellow]")
            return
        
        # Print as formatted JSON
        console.print("\n[bold blue]Firebase Data:[/bold blue]")
        print_json(json.dumps(data, indent=2, ensure_ascii=False))
        
        # If it's vocabulary data, also show as table
        if path and 'vocabulary' in path:
            console.print("\n[bold blue]Vocabulary Table:[/bold blue]")
            table = Table(show_header=True)
            table.add_column("Hiragana", style="bold")
            table.add_column("Kanji", style="cyan")
            table.add_column("French", style="green")
            table.add_column("Example", style="yellow")
            
            for word_id, word_data in data.items():
                table.add_row(
                    word_data.get('hiragana', ''),
                    word_data.get('kanji', ''),
                    word_data.get('french', ''),
                    word_data.get('example_sentence', '')[:50] + '...' if word_data.get('example_sentence', '') else ''
                )
            
            console.print(table)
        
        # If it's progress data, show as table
        elif path and 'progress' in path:
            console.print("\n[bold blue]Progress Table:[/bold blue]")
            table = Table(show_header=True)
            table.add_column("Word", style="bold")
            table.add_column("Attempts", style="cyan")
            table.add_column("Successes", style="green")
            table.add_column("Success Rate", style="yellow")
            table.add_column("Last Seen", style="magenta")
            
            for word, progress in data.items():
                attempts = progress.get('attempts', 0)
                successes = progress.get('successes', 0)
                success_rate = f"{(successes/attempts*100):.1f}%" if attempts > 0 else "0%"
                
                table.add_row(
                    word,
                    str(attempts),
                    str(successes),
                    success_rate,
                    progress.get('last_seen', 'Never')
                )
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error viewing data: {str(e)}[/red]")

if __name__ == "__main__":
    # Example usage
    console = Console()
    console.print("\n[bold blue]Firebase Data Viewer[/bold blue]")
    console.print("[dim]Available paths:[/dim]")
    console.print("1. [cyan]/[/cyan] (root)")
    console.print("2. [cyan]/vocabulary/{user_id}[/cyan] (vocabulary data)")
    console.print("3. [cyan]/progress/{user_id}[/cyan] (progress data)")
    
    path = input("\nEnter path to view (or press Enter for root): ").strip()
    view_data(path if path else None) 