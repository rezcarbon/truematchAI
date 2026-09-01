#!/bin/bash

# Interactive R2 Environment Setup Script
# Guides user through getting and setting R2 credentials

echo "🚀 Cloudflare R2 Environment Setup"
echo "===================================="
echo ""

# Check if credentials already set
if [ -n "$CLOUDFLARE_ACCOUNT_ID" ]; then
    echo "✅ CLOUDFLARE_ACCOUNT_ID already set"
    echo "   Value: ${CLOUDFLARE_ACCOUNT_ID:0:20}..."
else
    echo "❌ CLOUDFLARE_ACCOUNT_ID not set"
fi

if [ -n "$CLOUDFLARE_R2_ACCESS_KEY" ]; then
    echo "✅ CLOUDFLARE_R2_ACCESS_KEY already set"
    echo "   Value: ${CLOUDFLARE_R2_ACCESS_KEY:0:20}..."
else
    echo "❌ CLOUDFLARE_R2_ACCESS_KEY not set"
fi

if [ -n "$CLOUDFLARE_R2_SECRET_KEY" ]; then
    echo "✅ CLOUDFLARE_R2_SECRET_KEY already set"
    echo "   Value: (hidden for security)"
else
    echo "❌ CLOUDFLARE_R2_SECRET_KEY not set"
fi

echo ""
echo "📋 How to get your credentials:"
echo "1. Go to https://dash.cloudflare.com"
echo "2. Storage & databases → R2"
echo "3. Click your 'pokemontcg' bucket"
echo "4. Copy Account ID from the URL"
echo "5. Go to Account → API Tokens → R2"
echo "6. Create new token with Object Read/Write permission"
echo "7. Copy Access Key ID and Secret Access Key"
echo ""

read -p "Ready to enter credentials? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Skipping setup. Run this script again when ready."
    exit 1
fi

echo ""
echo "Enter your credentials (or press Enter to skip):"
echo ""

read -p "Account ID: " ACCOUNT_ID
read -p "Access Key ID: " ACCESS_KEY
read -sp "Secret Access Key: " SECRET_KEY
echo ""

if [ -z "$ACCOUNT_ID" ] || [ -z "$ACCESS_KEY" ] || [ -z "$SECRET_KEY" ]; then
    echo "❌ Credentials incomplete. Aborting."
    exit 1
fi

# Determine shell profile
if [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
    SHELL_NAME="bash"
else
    echo "❌ Could not find shell profile (.zshrc or .bashrc)"
    exit 1
fi

echo ""
echo "Adding credentials to $SHELL_PROFILE..."
echo ""

# Add credentials to shell profile
{
    echo ""
    echo "# Cloudflare R2 Credentials (Added $(date))"
    echo "export CLOUDFLARE_ACCOUNT_ID=\"$ACCOUNT_ID\""
    echo "export CLOUDFLARE_R2_ACCESS_KEY=\"$ACCESS_KEY\""
    echo "export CLOUDFLARE_R2_SECRET_KEY=\"$SECRET_KEY\""
} >> "$SHELL_PROFILE"

echo "✅ Credentials added to $SHELL_PROFILE"
echo ""

# Reload shell profile
if [ "$SHELL_NAME" = "zsh" ]; then
    source "$HOME/.zshrc"
    echo "✅ Reloaded zsh configuration"
elif [ "$SHELL_NAME" = "bash" ]; then
    source "$HOME/.bashrc"
    echo "✅ Reloaded bash configuration"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Verify credentials are set:"
echo "  echo \$CLOUDFLARE_ACCOUNT_ID"
echo "  echo \$CLOUDFLARE_R2_ACCESS_KEY"
echo ""
echo "Next: Run the upload script"
echo "  node ~/Documents/parallel-upload-r2.js"
echo ""
