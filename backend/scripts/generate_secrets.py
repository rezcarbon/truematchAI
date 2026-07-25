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
    logger.info("=" * 70)
    logger.info("TrueMatch Backend Secrets Generator")
    logger.info("=" * 70)
    logger.info()
    logger.info("IMPORTANT:")
    logger.info("- Keep these secrets secure; store in a secrets manager")
    logger.info("- Never commit .env file to git")
    logger.info("- Different environments (dev, staging, prod) need different secrets")
    logger.info("- Use these values in .env or deployment secrets (AWS Secrets Manager, etc.)")
    logger.info()
    logger.info("=" * 70)
    logger.info()

    # Generate secrets
    secrets = SecretGenerator.generate_all_secrets()

    # Display in .env format
    logger.info("# Copy these to your .env file or secrets manager:")
    logger.info()
    logger.info(f"ENCRYPTION_KEY={secrets['ENCRYPTION_KEY']}")
    logger.info(f"ENCRYPTION_INDEX_KEY={secrets['ENCRYPTION_INDEX_KEY']}")
    logger.info(f"JWT_SECRET={secrets['JWT_SECRET']}")
    logger.info()

    # Additional guidance
    logger.info("=" * 70)
    logger.info("NEXT STEPS:")
    logger.info("=" * 70)
    logger.info()
    logger.info("1. Copy the secrets above to your .env file:")
    logger.info("   cp .env.example .env")
    logger.info("   # Edit .env and paste the secrets above")
    logger.info()
    logger.info("2. For AWS deployments, store in AWS Secrets Manager:")
    logger.info("   aws secretsmanager create-secret \\")
    logger.info("     --name truematch/prod/encryption-key \\")
    logger.info("     --secret-string <ENCRYPTION_KEY>")
    logger.info()
    logger.info("3. For Docker, pass as environment variables:")
    logger.info("   docker run \\")
    logger.info("     -e ENCRYPTION_KEY=<secret> \\")
    logger.info("     -e ENCRYPTION_INDEX_KEY=<secret> \\")
    logger.info("     -e JWT_SECRET=<secret> \\")
    logger.info("     truematch-backend:latest")
    logger.info()
    logger.info("4. For Kubernetes, create a secret:")
    logger.info("   kubectl create secret generic truematch-secrets \\")
    logger.info("     --from-literal=ENCRYPTION_KEY=<secret> \\")
    logger.info("     --from-literal=ENCRYPTION_INDEX_KEY=<secret> \\")
    logger.info("     --from-literal=JWT_SECRET=<secret>")
    logger.info()
    logger.info("5. Verify configuration before deployment:")
    logger.info("   python -c \"from app.core.config_validator import SecretValidator; \\")
    logger.info("   from app.config import settings; \\")
    logger.info("   SecretValidator(settings).validate_all()\"")
    logger.info()


if __name__ == "__main__":
    main()
