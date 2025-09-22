#!/usr/bin/env python3
"""
Script to create a dummy user for testing the authentication flow.
This script creates a user that can be used for login testing.
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

def create_dummy_user():
    """Create a dummy user for testing."""
    try:
        # Create database engine
        engine = create_engine(settings.database_url)
        
        # Create tables if they don't exist
        BaseModel.metadata.create_all(bind=engine)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "test51214@yopmail.com").first()
        if existing_user:
            print("Dummy user already exists!")
            print(f"Email: {existing_user.email}")
            print(f"Name: {existing_user.full_name}")
            print(f"Active: {existing_user.is_active}")
            return
        
        # Create dummy user with simplified schema
        dummy_user = User(
            email="test51214@yopmail.com",
            password=security_config.hash_password("TestPassword123!"),
            first_name="Test",
            last_name="User",
            profile_picture="https://via.placeholder.com/150",
            primary_number="+1234567890",
            secondary_number="+0987654321",
            timezone="UTC",
            is_active=True
        )
        
        # Add to database
        db.add(dummy_user)
        db.commit()
        db.refresh(dummy_user)
        
        print("✅ Dummy user created successfully!")
        print(f"Email: {dummy_user.email}")
        print(f"Password: TestPassword123!")
        print(f"Name: {dummy_user.full_name}")
        print(f"User ID: {dummy_user.id}")
        print(f"Active: {dummy_user.is_active}")
        print(f"Timezone: {dummy_user.timezone}")
        print(f"Primary Number: {dummy_user.primary_number}")
        print(f"Profile Picture: {dummy_user.profile_picture}")
        print("\nYou can now use these credentials to test the login flow.")
        
    except Exception as e:
        print(f"❌ Error creating dummy user: {e}")
        sys.exit(1)
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("Creating dummy user for testing...")
    create_dummy_user()
