#!/usr/bin/env python3
"""
Example script showing how to use the S3 service for file operations.
This demonstrates the main S3 service methods and their usage.
"""

import os
import sys
from io import BytesIO

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.s3_service import s3_service

def example_upload_file():
    """Example: Upload a file to S3."""
    print("📤 Example: Uploading a file to S3")
    
    # Create a sample file content
    file_content = b"Hello, S3! This is a test file."
    file_obj = BytesIO(file_content)
    
    # Upload to S3
    s3_key = "examples/hello_world.txt"
    s3_url = s3_service.upload_file(
        file_obj=file_obj,
        key=s3_key,
        content_type="text/plain",
        metadata={
            "example": "true",
            "author": "S3 Integration Example"
        }
    )
    
    print(f"✅ File uploaded!")
    print(f"   S3 Key: {s3_key}")
    print(f"   S3 URL: {s3_url}")
    return s3_key

def example_upload_from_path():
    """Example: Upload a file from local path."""
    print("\n📤 Example: Uploading from local file path")
    
    # Create a temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("This is a temporary file for S3 upload example.")
        temp_file_path = f.name
    
    try:
        # Upload from path
        s3_key = "examples/temp_file.txt"
        s3_url = s3_service.upload_file_from_path(
            file_path=temp_file_path,
            key=s3_key,
            content_type="text/plain"
        )
        
        print(f"✅ File uploaded from path!")
        print(f"   Local Path: {temp_file_path}")
        print(f"   S3 Key: {s3_key}")
        print(f"   S3 URL: {s3_url}")
        return s3_key
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)

def example_download_file(s3_key):
    """Example: Download a file from S3."""
    print(f"\n📥 Example: Downloading file from S3")
    
    # Download file
    file_content = s3_service.download_file(s3_key)
    
    print(f"✅ File downloaded!")
    print(f"   Content length: {len(file_content)} bytes")
    print(f"   Content: {file_content.decode('utf-8')}")
    return file_content

def example_stream_file(s3_key):
    """Example: Stream a file from S3."""
    print(f"\n🌊 Example: Streaming file from S3")
    
    # Get file stream
    stream = s3_service.get_file_stream(s3_key)
    
    # Read stream in chunks
    content = b""
    chunk_size = 1024
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        content += chunk
    
    print(f"✅ File streamed!")
    print(f"   Content length: {len(content)} bytes")
    print(f"   Content: {content.decode('utf-8')}")

def example_get_file_info(s3_key):
    """Example: Get file information."""
    print(f"\n📋 Example: Getting file information")
    
    # Get file info
    file_info = s3_service.get_file_info(s3_key)
    
    print(f"✅ File info retrieved!")
    print(f"   Key: {file_info['key']}")
    print(f"   Size: {file_info['size']} bytes")
    print(f"   Content Type: {file_info['content_type']}")
    print(f"   Last Modified: {file_info['last_modified']}")
    print(f"   ETag: {file_info['etag']}")
    print(f"   Metadata: {file_info['metadata']}")

def example_list_files():
    """Example: List files in S3."""
    print(f"\n📂 Example: Listing files in S3")
    
    # List files with prefix
    result = s3_service.list_files(prefix="examples/", max_keys=10)
    
    print(f"✅ Files listed!")
    print(f"   Total files: {len(result['files'])}")
    print(f"   Is truncated: {result['is_truncated']}")
    
    for file_info in result['files']:
        print(f"   - {file_info['key']} ({file_info['size']} bytes)")

def example_presigned_url(s3_key):
    """Example: Generate presigned URL."""
    print(f"\n🔗 Example: Generating presigned URL")
    
    # Generate presigned URL for download
    presigned_url = s3_service.get_presigned_url(
        key=s3_key,
        expiration=3600,  # 1 hour
        http_method='get_object'
    )
    
    print(f"✅ Presigned URL generated!")
    print(f"   URL: {presigned_url[:100]}...")
    print(f"   Expires in: 1 hour")

def example_copy_file(s3_key):
    """Example: Copy a file within S3."""
    print(f"\n📋 Example: Copying file within S3")
    
    # Copy file to new location
    new_s3_key = f"{s3_key}.copy"
    new_url = s3_service.copy_file(
        source_key=s3_key,
        dest_key=new_s3_key,
        metadata={"copied_from": s3_key}
    )
    
    print(f"✅ File copied!")
    print(f"   Source: {s3_key}")
    print(f"   Destination: {new_s3_key}")
    print(f"   New URL: {new_url}")
    return new_s3_key

def example_delete_file(s3_key):
    """Example: Delete a file from S3."""
    print(f"\n🗑️  Example: Deleting file from S3")
    
    # Delete file
    result = s3_service.delete_file(s3_key)
    
    if result:
        print(f"✅ File deleted!")
        print(f"   Key: {s3_key}")
    else:
        print(f"❌ Failed to delete file: {s3_key}")

def example_extract_s3_key():
    """Example: Extract S3 key from URL."""
    print(f"\n🔍 Example: Extracting S3 key from URL")
    
    # Example S3 URL
    s3_url = "https://plugs-bucket.s3.us-east-1.amazonaws.com/examples/hello_world.txt"
    
    # Extract key
    s3_key = s3_service.extract_s3_key_from_url(s3_url)
    
    print(f"✅ S3 key extracted!")
    print(f"   URL: {s3_url}")
    print(f"   Key: {s3_key}")

def main():
    """Run all S3 service examples."""
    print("🚀 S3 Service Usage Examples")
    print("=" * 50)
    
    try:
        # Example 1: Upload file
        s3_key1 = example_upload_file()
        
        # Example 2: Upload from path
        s3_key2 = example_upload_from_path()
        
        # Example 3: Download file
        example_download_file(s3_key1)
        
        # Example 4: Stream file
        example_stream_file(s3_key1)
        
        # Example 5: Get file info
        example_get_file_info(s3_key1)
        
        # Example 6: List files
        example_list_files()
        
        # Example 7: Generate presigned URL
        example_presigned_url(s3_key1)
        
        # Example 8: Copy file
        s3_key_copy = example_copy_file(s3_key1)
        
        # Example 9: Extract S3 key from URL
        example_extract_s3_key()
        
        # Example 10: Delete files (cleanup)
        print(f"\n🧹 Cleaning up...")
        example_delete_file(s3_key1)
        example_delete_file(s3_key2)
        example_delete_file(s3_key_copy)
        
        print(f"\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
