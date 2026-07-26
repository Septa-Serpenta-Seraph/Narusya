#!/bin/bash
# Discord Login Automation for Narusya
# This script coordinates the login and channel check

echo "=== Discord Auto-Login Script ==="
echo "Reading credentials from secure storage..."

# Extract credentials (silent)
EMAIL=$(grep '^EMAIL=' ~/.hermes/secrets/narusya_account.enc | cut -d= -f2)
PASSWORD=$(grep '^PASSWORD=' ~/.hermes/secrets/narusya_account.enc | cut -d= -f2)

if [ -z "$EMAIL" ] || [ -z "$PASSWORD" ]; then
    echo "ERROR: Could not read credentials"
    exit 1
fi

echo "Credentials loaded for: $EMAIL"
echo ""
echo "Next steps:"
echo "1. Navigate to Discord login"
echo "2. Inject credentials via JavaScript"
echo "3. Navigate to Signal Front general chat"
echo "4. Capture recent messages"
echo ""
echo "Run this from a Hermes session with browser tools active."
