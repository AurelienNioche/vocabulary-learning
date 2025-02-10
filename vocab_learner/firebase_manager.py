from firebase_admin import credentials, db, auth
import firebase_admin
from rich.console import Console

class FirebaseManager:
    def __init__(self, cred_path, db_url):
        self.console = Console()
        self.initialize_firebase(cred_path, db_url)
    
    def initialize_firebase(self, cred_path, db_url):
        try:
            app = firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(cred, {
                'databaseURL': db_url
            })
        return app

    def get_user(self, email):
        try:
            return auth.get_user_by_email(email)
        except auth.UserNotFoundError:
            self.console.print(f"[red]User not found: {email}[/red]")
            return None
