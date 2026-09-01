#!/bin/bash
# Production configuration validator
# Ensures all critical environment variables are set before deployment

set -e

echo "🔍 Validating TrueMatch Production Configuration..."
echo ""

# Define required variables for production
REQUIRED_VARS=(
    "DATABASE_URL"
    "ANTHROPIC_API_KEY"
    "JWT_SECRET"
    "ENCRYPTION_KEY"
    "ENCRYPTION_INDEX_KEY"
)

# Define optional but recommended variables
OPTIONAL_VARS=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "REDIS_URL"
    "SENTRY_DSN"
)

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

MISSING_REQUIRED=()
MISSING_OPTIONAL=()

# Check required variables
echo "📋 Checking required environment variables..."
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_REQUIRED+=("$var")
        echo -e "${RED}✗${NC} $var - NOT SET"
    else
        echo -e "${GREEN}✓${NC} $var - SET"
    fi
done

echo ""
echo "📋 Checking optional environment variables..."
for var in "${OPTIONAL_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_OPTIONAL+=("$var")
        echo -e "${YELLOW}⚠${NC}  $var - NOT SET (optional)"
    else
        echo -e "${GREEN}✓${NC} $var - SET"
    fi
done

echo ""
echo "🔐 Validating configuration quality..."

# Validate JWT_SECRET length
if [ -n "${JWT_SECRET}" ]; then
    JWT_LEN=${#JWT_SECRET}
    if [ $JWT_LEN -lt 32 ]; then
        echo -e "${RED}✗${NC} JWT_SECRET too short ($JWT_LEN chars, need 32+)"
        MISSING_REQUIRED+=("JWT_SECRET_TOO_SHORT")
    else
        echo -e "${GREEN}✓${NC} JWT_SECRET length: $JWT_LEN characters (minimum 32)"
    fi
fi

# Validate ENCRYPTION_KEY format
if [ -n "${ENCRYPTION_KEY}" ]; then
    # Try to decode as base64 or hex
    if echo -n "$ENCRYPTION_KEY" | base64 -d >/dev/null 2>&1; then
        ENCRYPTION_BYTES=$(echo -n "$ENCRYPTION_KEY" | base64 -d | wc -c)
        if [ $ENCRYPTION_BYTES -lt 32 ]; then
            echo -e "${RED}✗${NC} ENCRYPTION_KEY too short ($ENCRYPTION_BYTES bytes, need 32)"
            MISSING_REQUIRED+=("ENCRYPTION_KEY_TOO_SHORT")
        else
            echo -e "${GREEN}✓${NC} ENCRYPTION_KEY valid base64 ($ENCRYPTION_BYTES bytes)"
        fi
    elif echo -n "$ENCRYPTION_KEY" | grep -E '^[0-9a-f]+$' >/dev/null 2>&1; then
        ENCRYPTION_BYTES=$((${#ENCRYPTION_KEY} / 2))
        if [ $ENCRYPTION_BYTES -lt 32 ]; then
            echo -e "${RED}✗${NC} ENCRYPTION_KEY too short ($ENCRYPTION_BYTES bytes, need 32)"
            MISSING_REQUIRED+=("ENCRYPTION_KEY_TOO_SHORT")
        else
            echo -e "${GREEN}✓${NC} ENCRYPTION_KEY valid hex ($ENCRYPTION_BYTES bytes)"
        fi
    else
        echo -e "${RED}✗${NC} ENCRYPTION_KEY invalid format (must be base64 or hex)"
        MISSING_REQUIRED+=("ENCRYPTION_KEY_INVALID")
    fi
fi

# Validate DATABASE_URL format
if [ -n "${DATABASE_URL}" ]; then
    if [[ "$DATABASE_URL" == postgresql* ]]; then
        echo -e "${GREEN}✓${NC} DATABASE_URL format valid (postgresql)"
    else
        echo -e "${RED}✗${NC} DATABASE_URL must start with 'postgresql'"
        MISSING_REQUIRED+=("DATABASE_URL_INVALID")
    fi
fi

# Validate Anthropic API key format
if [ -n "${ANTHROPIC_API_KEY}" ]; then
    if [[ "$ANTHROPIC_API_KEY" == sk-ant-* ]]; then
        echo -e "${GREEN}✓${NC} ANTHROPIC_API_KEY format valid"
    else
        echo -e "${RED}✗${NC} ANTHROPIC_API_KEY should start with 'sk-ant-'"
        MISSING_REQUIRED+=("ANTHROPIC_API_KEY_INVALID")
    fi
fi

echo ""
echo "🧪 Running Python configuration validator..."
python3 << 'PYTHON_SCRIPT'
import sys
import os

try:
    from app.core.config_validator import SecretValidator
    from app.config import settings

    print("✓ Configuration module loaded")

    validator = SecretValidator(settings)
    validator.validate_all()

    print("✓ All configuration validations passed")
    sys.exit(0)
except ValueError as e:
    print(f"✗ Configuration validation failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
PYTHON_SCRIPT

PYTHON_EXIT=$?

echo ""
echo "════════════════════════════════════════════════════════════"

# Report summary
if [ ${#MISSING_REQUIRED[@]} -eq 0 ] && [ $PYTHON_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    echo ""
    if [ ${#MISSING_OPTIONAL[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠  ${#MISSING_OPTIONAL[@]} optional variables not set:${NC}"
        for var in "${MISSING_OPTIONAL[@]}"; do
            echo "   - $var"
        done
        echo ""
        echo "These are optional. Set them for full functionality."
    fi
    echo -e "${GREEN}✓ Ready for production deployment!${NC}"
    exit 0
else
    echo -e "${RED}✗ Configuration validation failed${NC}"
    echo ""
    echo -e "${RED}Missing or invalid required variables (${#MISSING_REQUIRED[@]}):${NC}"
    for var in "${MISSING_REQUIRED[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Set all required variables before deploying to production."
    exit 1
fi
