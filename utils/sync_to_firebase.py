import os
from pathlib import Path
import json
import firebase_admin
from firebase_admin import credentials, db, auth
from dotenv import load_dotenv
from rich.console import Console

def sync_to_firebase():
    console = Console()
    console.print("\n[bold blue]=== Starting Firebase Sync ===[/bold blue]")
    
    # Load environment variables
    load_dotenv()
    cred_path = os.path.expandvars(os.getenv('FIREBASE_CREDENTIALS_PATH'))
    
    if not os.path.exists(cred_path):
        console.print(f"[red]Error: Firebase credentials not found at {cred_path}[/red]")
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
            console.print("[red]Error: Firebase user credentials not found in .env file[/red]")
            return
        
        # Get user ID
        user = auth.get_user_by_email(email)
        user_id = user.uid
        
        # Set up database references
        vocab_ref = db.reference(f'/vocabulary/{user_id}')
        
        # Read local vocabulary
        json_path = Path("data/vocabulary.json")
        if not json_path.exists():
            console.print("[red]Error: vocabulary.json not found[/red]")
            return
            
        with open(json_path, 'r', encoding='utf-8') as f:
            vocab_data = json.load(f)
        
        # Upload to Firebase
        console.print("[dim gray]Uploading vocabulary to Firebase...[/dim gray]")
        vocab_ref.set(vocab_data)
        
        # Verify upload
        uploaded_data = vocab_ref.get()
        if not uploaded_data:
            raise Exception("Failed to verify uploaded data")
        
        # Compare word counts
        local_count = len(vocab_data)
        uploaded_count = len(uploaded_data)
        
        if local_count != uploaded_count:
            console.print(f"[yellow]Warning: Word count mismatch. Local: {local_count}, Firebase: {uploaded_count}[/yellow]")
        else:
            console.print(f"[green]✓ Successfully synced {local_count} words to Firebase![/green]")
        
    except Exception as e:
        console.print(f"[red]Error during Firebase sync: {str(e)}[/red]")

if __name__ == "__main__":
    sync_to_firebase() 