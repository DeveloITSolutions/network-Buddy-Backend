#!/usr/bin/env python3
"""
Test script for media upload functionality.
"""
import requests
import json
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
JWT_TOKEN = "YOUR_JWT_TOKEN_HERE"  # Replace with actual token
EVENT_ID = "YOUR_EVENT_ID_HERE"    # Replace with actual event ID

def test_media_upload():
    """Test media upload with different file types."""
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}"
    }
    
    # Test data
    test_files = [
        {
            "file_path": "test_image.jpg",
            "title": "Test Image",
            "description": "Test image upload",
            "tags": "test,image,upload"
        },
        {
            "file_path": "test_document.pdf", 
            "title": "Test Document",
            "description": "Test document upload",
            "tags": "test,document,upload"
        }
    ]
    
    print("Testing Media Upload API...")
    print("=" * 50)
    
    for test_file in test_files:
        print(f"\nTesting upload: {test_file['file_path']}")
        
        # Check if test file exists
        if not os.path.exists(test_file['file_path']):
            print(f"❌ Test file not found: {test_file['file_path']}")
            print("   Create a test file or update the file path")
            continue
        
        # Prepare form data
        files = {
            'file': (test_file['file_path'], open(test_file['file_path'], 'rb'))
        }
        
        data = {
            'title': test_file['title'],
            'description': test_file['description'],
            'tags': test_file['tags']
        }
        
        try:
            # Make request
            response = requests.post(
                f"{BASE_URL}/api/v1/events/{EVENT_ID}/media",
                headers=headers,
                files=files,
                data=data
            )
            
            # Close file
            files['file'][1].close()
            
            # Check response
            if response.status_code == 201:
                result = response.json()
                print(f"✅ Upload successful!")
                print(f"   Media ID: {result.get('id')}")
                print(f"   File URL: {result.get('file_url')}")
                print(f"   File Type: {result.get('file_type')}")
                print(f"   File Size: {result.get('file_size')} bytes")
            else:
                print(f"❌ Upload failed!")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

def test_json_upload():
    """Test JSON-based media upload (backward compatibility)."""
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "title": "External Media",
        "description": "Test JSON upload with external URL",
        "file_url": "https://example.com/sample.jpg",
        "file_type": "image/jpeg",
        "file_size": 1024000,
        "tags": ["test", "json", "external"]
    }
    
    print("\nTesting JSON Upload API...")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/events/{EVENT_ID}/media/json",
            headers=headers,
            json=data
        )
        
        if response.status_code == 201:
            result = response.json()
            print("✅ JSON upload successful!")
            print(f"   Media ID: {result.get('id')}")
            print(f"   File URL: {result.get('file_url')}")
        else:
            print(f"❌ JSON upload failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_get_media():
    """Test getting event media."""
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}"
    }
    
    print("\nTesting Get Media API...")
    print("=" * 50)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/events/{EVENT_ID}/media",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Retrieved {len(result)} media items")
            for item in result:
                print(f"   - {item.get('title')} ({item.get('file_type')})")
        else:
            print(f"❌ Get media failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def create_test_files():
    """Create test files for upload testing."""
    
    print("Creating test files...")
    
    # Create a simple test image (1x1 pixel JPEG)
    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    with open("test_image.jpg", "wb") as f:
        f.write(test_image_data)
    
    # Create a simple test PDF
    test_pdf_data = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF'
    
    with open("test_document.pdf", "wb") as f:
        f.write(test_pdf_data)
    
    print("✅ Test files created: test_image.jpg, test_document.pdf")

if __name__ == "__main__":
    print("Media Upload Test Script")
    print("=" * 50)
    
    # Check if JWT token and event ID are set
    if JWT_TOKEN == "YOUR_JWT_TOKEN_HERE" or EVENT_ID == "YOUR_EVENT_ID_HERE":
        print("❌ Please set JWT_TOKEN and EVENT_ID in the script")
        print("   Edit the script and replace the placeholder values")
        exit(1)
    
    # Create test files
    create_test_files()
    
    # Run tests
    test_media_upload()
    test_json_upload()
    test_get_media()
    
    # Cleanup
    print("\nCleaning up test files...")
    for file in ["test_image.jpg", "test_document.pdf"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"   Removed {file}")
    
    print("\nTest completed!")
