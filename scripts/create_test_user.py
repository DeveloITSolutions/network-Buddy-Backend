#!/usr/bin/env python3
"""
Script to create a test user with specific credentials.
This script creates a user that can be used for testing the authentication flow.
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from app.config.security import security_config
from app.models.user import User
from app.models.base import BaseModel
from app.utils.datetime import get_current_utc_time

def create_test_user():
    """Create a test user with specific credentials."""
    try:
        # Create database engine
        engine = create_engine(settings.database_url)
        
        # Create tables if they don't exist
        BaseModel.metadata.create_all(bind=engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # User credentials
        email = "dr.tiff@socailabs.com"
        password = "Davis-1986"
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print("Test user already exists!")
            print(f"Email: {existing_user.email}")
            print(f"Name: {existing_user.full_name}")
            print(f"Active: {existing_user.is_active}")
            print(f"User ID: {existing_user.id}")
            
            # Ask if user wants to update password
            response = input("\nDo you want to update the password? (y/n): ").lower().strip()
            if response == 'y' or response == 'yes':
                existing_user.password = security_config.hash_password(password)
                existing_user.updated_at = get_current_utc_time()
                db.commit()
                db.refresh(existing_user)
                print("✅ Password updated successfully!")
            return
        
        # Create test user with specified credentials
        test_user = User(
            email=email,
            password=security_config.hash_password(password),
            first_name="Test",
            last_name="User",
            profile_picture="https://via.placeholder.com/150",
            primary_number="+1234567890",
            secondary_number="+0987654321",
            timezone="UTC",
            is_active=True
        )
        
        # Add to database
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print("✅ Test user created successfully!")
        print(f"Email: {test_user.email}")
        print(f"Password: {password}")
        print(f"Name: {test_user.full_name}")
        print(f"User ID: {test_user.id}")
        print(f"Active: {test_user.is_active}")
        print(f"Timezone: {test_user.timezone}")
        print(f"Primary Number: {test_user.primary_number}")
        print(f"Profile Picture: {test_user.profile_picture}")
        print(f"Created At: {test_user.created_at}")
        print("\nYou can now use these credentials to test the login flow:")
        print(f"Email: {email}")
        print(f"Password: {password}")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        sys.exit(1)
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("Creating test user with specified credentials...")
    print("Email: test51214@yopmail.com")
    print("Password: NewSecurePassword123")
    print("-" * 50)
    create_test_user()
