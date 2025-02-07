import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db, auth
from datetime import datetime

def test_firebase_connection():
    print("\n=== Firebase Connection Test ===\n")
    
    # 1. Load environment variables
    print("1. Loading environment variables...")
    load_dotenv()
    cred_path = os.path.expandvars(os.getenv('FIREBASE_CREDENTIALS_PATH'))
    db_url = os.getenv('FIREBASE_DATABASE_URL')
    email = os.getenv('FIREBASE_USER_EMAIL')
    password = os.getenv('FIREBASE_USER_PASSWORD')
    
    print(f"Credentials path: {cred_path}")
    print(f"Database URL: {db_url}")
    print(f"Email configured: {email is not None}")
    print(f"Password configured: {password is not None}")
    
    # 2. Check if credentials file exists
    if not os.path.exists(cred_path):
        print(f"\nERROR: Credentials file not found at {cred_path}")
        return False
    
    try:
        # 3. Initialize Firebase
        print("\n2. Initializing Firebase...")
        cred = credentials.Certificate(cred_path)
        
        # Check if app is already initialized
        try:
            firebase_admin.get_app()
            print("Firebase app already initialized")
        except ValueError:
            firebase_admin.initialize_app(cred, {
                'databaseURL': db_url
            })
            print("Firebase app initialized successfully")
        
        # 4. Authenticate user
        print("\n3. Authenticating user...")
        user = auth.get_user_by_email(email)
        user_id = user.uid
        print(f"User authenticated successfully (UID: {user_id})")
        
        # 5. Test database connection
        print("\n4. Testing database connection...")
        db_ref = db.reference(f'/progress/{user_id}')
        test_ref = db_ref.child('_connection_test')
        timestamp = datetime.now().isoformat()
        test_ref.set({'timestamp': timestamp})
        
        # 6. Verify data was written
        print("\n5. Verifying data...")
        read_data = test_ref.get()
        if read_data and read_data.get('timestamp') == timestamp:
            print("Data written and read successfully!")
        else:
            print("ERROR: Data verification failed!")
            return False
        
        print("\n=== All Tests Passed! ===")
        return True
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_firebase_connection() 