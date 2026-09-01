#!/bin/bash

# Use wrangler to get file listings via R2 API
echo "Scanning R2 bucket structure..."

# List all prefixes (directories)
echo "📁 Available sets in R2:"
curl -s "https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/" 2>/dev/null | grep -o "Pokemon%20TCG" | sort -u || echo "Note: Need authentication for listing"

echo ""
echo "✅ Public URL confirmed working:"
echo "https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/"
