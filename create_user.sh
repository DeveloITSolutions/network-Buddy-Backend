#!/bin/bash

# Script to create a test user in the Docker container
# Usage: ./create_user.sh

echo "Creating test user with specified credentials..."
echo "Email: test51214@yopmail.com"
echo "Password: NewSecurePassword123"
echo "----------------------------------------"

# Run the script inside the API container
docker exec the_plugs_api python /app/scripts/create_test_user.py

echo ""
echo "✅ User creation script completed!"
echo ""
echo "You can now test the login with:"
echo "curl -X POST http://localhost:8000/api/v1/auth/login \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"email\": \"test51214@yopmail.com\", \"password\": \"NewSecurePassword123\"}'"
