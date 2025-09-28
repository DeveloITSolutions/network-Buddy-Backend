#!/usr/bin/env python3
"""
Robust script to create a test user with proper password hashing.
This script handles bcrypt compatibility issues and ensures proper password verification.
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config.database import db_config
from app.config.security import security_config
from app.models.user import User
from app.utils.datetime import get_current_utc_time

def create_or_update_user():
    """Create or update a test user with robust password handling."""
    try:
        # Use existing database configuration
        db = next(db_config.get_session())
        
        # User credentials
        email = "test51214@yopmail.com"
        password = "NewSecurePassword123"
        
        print(f"Creating/updating user with email: {email}")
        print(f"Password: {password}")
        print("-" * 50)
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            print("✅ User already exists!")
            print(f"Email: {existing_user.email}")
            print(f"Name: {existing_user.full_name}")
            print(f"User ID: {existing_user.id}")
            print(f"Current hash: {existing_user.password[:20]}...")
            
            # Test current password verification
            current_verification = security_config.verify_password(password, existing_user.password)
            print(f"Current password verification: {'✅ PASS' if current_verification else '❌ FAIL'}")
            
            if not current_verification:
                print("\n🔄 Password verification failed. Updating password hash...")
                
                # Generate new hash
                new_hash = security_config.hash_password(password)
                
                # Test new hash verification
                new_verification = security_config.verify_password(password, new_hash)
                print(f"New hash verification test: {'✅ PASS' if new_verification else '❌ FAIL'}")
                
                if new_verification:
                    # Update user password
                    existing_user.password = new_hash
                    existing_user.updated_at = get_current_utc_time()
                    db.commit()
                    db.refresh(existing_user)
                    
                    print("✅ Password hash updated successfully!")
                    
                    # Final verification
                    final_test = security_config.verify_password(password, existing_user.password)
                    print(f"Final verification test: {'✅ PASS' if final_test else '❌ FAIL'}")
                else:
                    print("❌ New hash verification failed, not updating")
                    return False
            else:
                print("✅ Password verification working correctly!")
        else:
            print("Creating new user...")
            
            # Generate password hash
            password_hash = security_config.hash_password(password)
            
            # Test hash verification before saving
            hash_verification = security_config.verify_password(password, password_hash)
            print(f"Hash verification test: {'✅ PASS' if hash_verification else '❌ FAIL'}")
            
            if not hash_verification:
                print("❌ Password hash verification failed, cannot create user")
                return False
            
            # Create new user
            new_user = User(
                email=email,
                password=password_hash,
                first_name="Test",
                last_name="User",
                profile_picture="https://via.placeholder.com/150",
                primary_number="+1234567890",
                secondary_number="+0987654321",
                timezone="UTC",
                is_active=True
            )
            
            # Add to database
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            print("✅ User created successfully!")
            print(f"Email: {new_user.email}")
            print(f"Name: {new_user.full_name}")
            print(f"User ID: {new_user.id}")
            print(f"Active: {new_user.is_active}")
            print(f"Created At: {new_user.created_at}")
            
            # Final verification
            final_test = security_config.verify_password(password, new_user.password)
            print(f"Final verification test: {'✅ PASS' if final_test else '❌ FAIL'}")
        
        print("\n" + "=" * 50)
        print("🎉 User setup completed successfully!")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print("\nYou can now test the login with:")
        print(f"curl -X POST http://localhost:8000/api/v1/auth/login \\")
        print(f"  -H \"Content-Type: application/json\" \\")
        print(f"  -d '{{\"email\": \"{email}\", \"password\": \"{password}\"}}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in user creation/update: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("Creating/updating test user with robust password handling...")
    success = create_or_update_user()
    sys.exit(0 if success else 1)
