#!/usr/bin/env python3
"""Generate secure secrets for TrueMatch backend configuration.

Usage:
    python scripts/generate_secrets.py

Output: Prints secrets suitable for .env file

Example:
    python scripts/generate_secrets.py > /tmp/secrets.txt
    # Review /tmp/secrets.txt before adding to .env
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config_validator import SecretGenerator


def main() -> None:
    """Generate and print all required secrets."""
    print("=" * 70)
    print("TrueMatch Backend Secrets Generator")
    print("=" * 70)
    print()
    print("IMPORTANT:")
    print("- Keep these secrets secure; store in a secrets manager")
    print("- Never commit .env file to git")
    print("- Different environments (dev, staging, prod) need different secrets")
    print("- Use these values in .env or deployment secrets (AWS Secrets Manager, etc.)")
    print()
    print("=" * 70)
    print()

    # Generate secrets
    secrets = SecretGenerator.generate_all_secrets()

    # Display in .env format
    print("# Copy these to your .env file or secrets manager:")
    print()
    print(f"ENCRYPTION_KEY={secrets['ENCRYPTION_KEY']}")
    print(f"ENCRYPTION_INDEX_KEY={secrets['ENCRYPTION_INDEX_KEY']}")
    print(f"JWT_SECRET={secrets['JWT_SECRET']}")
    print()

    # Additional guidance
    print("=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print()
    print("1. Copy the secrets above to your .env file:")
    print("   cp .env.example .env")
    print("   # Edit .env and paste the secrets above")
    print()
    print("2. For AWS deployments, store in AWS Secrets Manager:")
    print("   aws secretsmanager create-secret \\")
    print("     --name truematch/prod/encryption-key \\")
    print("     --secret-string <ENCRYPTION_KEY>")
    print()
    print("3. For Docker, pass as environment variables:")
    print("   docker run \\")
    print("     -e ENCRYPTION_KEY=<secret> \\")
    print("     -e ENCRYPTION_INDEX_KEY=<secret> \\")
    print("     -e JWT_SECRET=<secret> \\")
    print("     truematch-backend:latest")
    print()
    print("4. For Kubernetes, create a secret:")
    print("   kubectl create secret generic truematch-secrets \\")
    print("     --from-literal=ENCRYPTION_KEY=<secret> \\")
    print("     --from-literal=ENCRYPTION_INDEX_KEY=<secret> \\")
    print("     --from-literal=JWT_SECRET=<secret>")
    print()
    print("5. Verify configuration before deployment:")
    print("   python -c \"from app.core.config_validator import SecretValidator; \\")
    print("   from app.config import settings; \\")
    print("   SecretValidator(settings).validate_all()\"")
    print()


if __name__ == "__main__":
    main()
