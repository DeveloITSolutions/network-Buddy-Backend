#!/bin/bash
# Script to update NGINX client_max_body_size for large file uploads

set -e

echo "=================================================="
echo "NGINX Body Size Update Script"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root or with sudo${NC}"
    exit 1
fi

# Backup existing config
NGINX_CONF="/etc/nginx/nginx.conf"
BACKUP_FILE="/etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)"

echo -e "${YELLOW}📋 Backing up current configuration...${NC}"
cp $NGINX_CONF $BACKUP_FILE
echo -e "${GREEN}✅ Backup created: $BACKUP_FILE${NC}"
echo ""

# Update or add client_max_body_size
echo -e "${YELLOW}🔧 Updating client_max_body_size...${NC}"

if grep -q "client_max_body_size" $NGINX_CONF; then
    echo "client_max_body_size found. Updating value..."
    sed -i 's/client_max_body_size .*/client_max_body_size 200M;/' $NGINX_CONF
else
    echo "client_max_body_size not found. Adding to http block..."
    sed -i '/http {/a \    # Maximum body size for file uploads\n    client_max_body_size 200M;\n    client_body_buffer_size 128k;\n    client_body_timeout 120s;' $NGINX_CONF
fi

echo -e "${GREEN}✅ Configuration updated${NC}"
echo ""

# Show the changes
echo -e "${YELLOW}📄 Current configuration:${NC}"
grep -A 2 "client_max_body_size" $NGINX_CONF || echo "Configuration added"
echo ""

# Test configuration
echo -e "${YELLOW}🧪 Testing NGINX configuration...${NC}"
if nginx -t 2>&1; then
    echo -e "${GREEN}✅ Configuration is valid${NC}"
    echo ""
    
    # Reload NGINX
    echo -e "${YELLOW}🔄 Reloading NGINX...${NC}"
    systemctl reload nginx
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ NGINX reloaded successfully!${NC}"
        echo ""
        echo -e "${GREEN}=================================================="
        echo "✅ Update Complete!"
        echo "=================================================="
        echo ""
        echo "NGINX is now configured to accept uploads up to 200MB"
        echo "Backup saved to: $BACKUP_FILE"
        echo ""
    else
        echo -e "${RED}❌ Failed to reload NGINX${NC}"
        echo "Restoring backup..."
        mv $BACKUP_FILE $NGINX_CONF
        systemctl reload nginx
        exit 1
    fi
else
    echo -e "${RED}❌ Configuration test failed!${NC}"
    echo "Restoring backup..."
    mv $BACKUP_FILE $NGINX_CONF
    exit 1
fi

# Display verification
echo -e "${YELLOW}📊 Verification:${NC}"
echo "Run this command to test file upload:"
echo ""
echo "curl -X POST 'https://your-domain.com/api/v1/events/{event_id}/media' \\"
echo "  -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "  -F 'files=@large-file.jpg' \\"
echo "  -F 'title=Test Upload'"
echo ""

