#!/usr/bin/env python3
"""
Test script for S3 integration.
Run this script to verify that S3 integration is working correctly.
"""

import os
import sys
import tempfile
from io import BytesIO

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.services.s3_service import s3_service
    from app.config.settings import settings
    print("✅ Successfully imported S3 service and settings")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    sys.exit(1)

def test_s3_connection():
    """Test basic S3 connection."""
    print("\n🔍 Testing S3 connection...")
    try:
        # Test connection by listing files
        result = s3_service.list_files(max_keys=1)
        print(f"✅ S3 connection successful!")
        print(f"   Bucket: {settings.s3_bucket_name}")
        print(f"   Region: {settings.s3_region}")
        print(f"   Files found: {len(result['files'])}")
        return True
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        return False

def test_file_upload():
    """Test file upload to S3."""
    print("\n📤 Testing file upload...")
    try:
        # Create a test file
        test_content = b"This is a test file for S3 integration."
        test_file = BytesIO(test_content)
        
        # Generate a test key
        s3_key = s3_service._generate_s3_key(
            prefix="test",
            filename="test_file.txt"
        )
        
        # Upload the file
        s3_url = s3_service.upload_file(
            file_obj=test_file,
            key=s3_key,
            content_type="text/plain",
            metadata={"test": "true", "purpose": "integration_test"}
        )
        
        print(f"✅ File uploaded successfully!")
        print(f"   S3 Key: {s3_key}")
        print(f"   S3 URL: {s3_url}")
        return s3_key, s3_url
    except Exception as e:
        print(f"❌ File upload failed: {e}")
        return None, None

def test_file_download(s3_key):
    """Test file download from S3."""
    print("\n📥 Testing file download...")
    try:
        # Download the file
        file_content = s3_service.download_file(s3_key)
        
        print(f"✅ File downloaded successfully!")
        print(f"   Content length: {len(file_content)} bytes")
        print(f"   Content preview: {file_content[:50].decode('utf-8')}...")
        return True
    except Exception as e:
        print(f"❌ File download failed: {e}")
        return False

def test_file_info(s3_key):
    """Test getting file info from S3."""
    print("\n📋 Testing file info retrieval...")
    try:
        # Get file info
        file_info = s3_service.get_file_info(s3_key)
        
        print(f"✅ File info retrieved successfully!")
        print(f"   Size: {file_info['size']} bytes")
        print(f"   Content Type: {file_info['content_type']}")
        print(f"   Metadata: {file_info['metadata']}")
        return True
    except Exception as e:
        print(f"❌ File info retrieval failed: {e}")
        return False

def test_file_deletion(s3_key):
    """Test file deletion from S3."""
    print("\n🗑️  Testing file deletion...")
    try:
        # Delete the file
        result = s3_service.delete_file(s3_key)
        
        if result:
            print(f"✅ File deleted successfully!")
            return True
        else:
            print(f"❌ File deletion failed: {result}")
            return False
    except Exception as e:
        print(f"❌ File deletion failed: {e}")
        return False

def test_presigned_url(s3_key):
    """Test presigned URL generation."""
    print("\n🔗 Testing presigned URL generation...")
    try:
        # Generate presigned URL
        presigned_url = s3_service.get_presigned_url(s3_key, expiration=3600)
        
        print(f"✅ Presigned URL generated successfully!")
        print(f"   URL length: {len(presigned_url)} characters")
        print(f"   URL starts with: {presigned_url[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Presigned URL generation failed: {e}")
        return False

def main():
    """Run all S3 integration tests."""
    print("🚀 Starting S3 Integration Tests")
    print("=" * 50)
    
    # Check configuration
    print(f"\n⚙️  Configuration:")
    print(f"   S3 Bucket: {settings.s3_bucket_name}")
    print(f"   S3 Region: {settings.s3_region}")
    print(f"   Max File Size: {settings.max_file_size} bytes")
    
    # Run tests
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Connection
    total_tests += 1
    if test_s3_connection():
        tests_passed += 1
    
    # Test 2: Upload
    total_tests += 1
    s3_key, s3_url = test_file_upload()
    if s3_key:
        tests_passed += 1
        
        # Test 3: Download
        total_tests += 1
        if test_file_download(s3_key):
            tests_passed += 1
        
        # Test 4: File Info
        total_tests += 1
        if test_file_info(s3_key):
            tests_passed += 1
        
        # Test 5: Presigned URL
        total_tests += 1
        if test_presigned_url(s3_key):
            tests_passed += 1
        
        # Test 6: Deletion
        total_tests += 1
        if test_file_deletion(s3_key):
            tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! S3 integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check your S3 configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
