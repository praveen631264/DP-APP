
import os
import sys
from datetime import datetime
from uuid import uuid4
from werkzeug.security import generate_password_hash
from mongoengine import connect

# Add the app directory to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.models import User, Role
from config import MONGO_URI, MONGO_DB_NAME

def create_test_user():
    """
    Connects to the database and creates a test user.
    """
    try:
        # 1. Connect to MongoDB
        print(f"Connecting to MongoDB at {MONGO_URI}...")
        connect(db=MONGO_DB_NAME, host=MONGO_URI)
        print("Connection successful.")

        # 2. Define user details
        test_email = "test@example.com"
        test_password = "password"

        # 3. Check if user already exists
        if User.objects(email=test_email).first():
            print(f"User with email {test_email} already exists. Aborting.")
            return

        # 4. Create and save the new user
        print(f"Creating user: {test_email}")
        user = User(
            email=test_email,
            password=generate_password_hash(test_password),
            active=True,  # User is active by default
            fs_uniquifier=str(uuid4()), # Required by Flask-Security
            confirmed_at=datetime.utcnow()
        )
        user.save()

        print("\n" + "="*30)
        print("Test user created successfully!")
        print(f"  Email: {test_email}")
        print(f"  Password: {test_password}")
        print("="*30 + "\n")

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    create_test_user()
