import os
from pathlib import Path
import json
import firebase_admin
from firebase_admin import credentials, db, auth
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm

def reset_progress():
    console = Console()
    console.print("\n[bold red]=== Progress Reset Tool ===[/bold red]")
    
    # Confirm with user
    if not Confirm.ask("[bold red]⚠️  WARNING: This will delete all learning progress. Are you sure?[/bold red]"):
        console.print("[yellow]Operation cancelled.[/yellow]")
        return
    
    # Load environment variables
    load_dotenv()
    cred_path = os.path.expandvars(os.getenv('FIREBASE_CREDENTIALS_PATH'))
    
    # Reset local progress file
    progress_path = Path("data/progress.json")
    if progress_path.exists():
        progress_path.unlink()
        console.print("[green]✓ Local progress file deleted[/green]")
    
    # Create empty progress file
    with open(progress_path, 'w', encoding='utf-8') as f:
        json.dump({}, f)
    console.print("[green]✓ Created empty progress file[/green]")
    
    # Reset Firebase progress
    if not os.path.exists(cred_path):
        console.print(f"[yellow]Warning: Firebase credentials not found at {cred_path}[/yellow]")
        return
    
    try:
        # Initialize Firebase
        try:
            app = firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(cred, {
                'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
            })
        
        # Get user credentials
        email = os.getenv('FIREBASE_USER_EMAIL')
        password = os.getenv('FIREBASE_USER_PASSWORD')
        
        if not email or not password:
            console.print("[yellow]Warning: Firebase user credentials not found in .env file[/yellow]")
            return
        
        # Get user ID
        user = auth.get_user_by_email(email)
        user_id = user.uid
        
        # Reset progress in Firebase
        progress_ref = db.reference(f'/progress/{user_id}')
        progress_ref.set({})
        console.print("[green]✓ Firebase progress reset[/green]")
        
        console.print("\n[bold green]✓ Progress has been completely reset![/bold green]")
        
    except Exception as e:
        console.print(f"[red]Error during Firebase reset: {str(e)}[/red]")

if __name__ == "__main__":
    reset_progress() 