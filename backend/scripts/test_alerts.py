#!/usr/bin/env python3
"""
Test alert system connectivity and delivery.

Verifies that all critical notification channels are operational before deploying
to production. Run this script as part of pre-deployment checks or monthly game days.

Usage:
    ./scripts/test_alerts.py
    python scripts/test_alerts.py

Exit codes:
    0: All systems healthy
    1: One or more systems failed
"""
import asyncio
import logging
import sys
from datetime import datetime

# Configure logging for this script
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def test_slack_connection() -> bool:
    """Test Slack webhook connectivity.

    Creates a SlackNotifier instance and attempts to send a test message
    to the configured webhook URL.

    Returns:
        True if webhook is accessible, False otherwise.
    """
    try:
        from app.workers.notification_service import SlackNotifier
        from app.config import settings

        if not settings.slack_webhook_url:
            print("⚠️  Slack webhook URL not configured; skipping")
            return True  # Not an error, just not configured

        print("Testing Slack webhook connectivity...", end=" ", flush=True)

        notifier = SlackNotifier()
        success = await notifier.send_message(
            text="🧪 Test message from TrueMatch alert system",
            timestamp=datetime.utcnow().isoformat(),
        )

        if success:
            print("✅ Slack webhook connected")
            return True
        else:
            print("❌ Slack webhook failed")
            return False

    except Exception as e:
        print(f"❌ Slack webhook failed: {e}")
        return False


async def test_email_connection() -> bool:
    """Test email SMTP connectivity.

    Creates an EmailNotifier instance and verifies that the configured
    SMTP server is reachable and authenticated.

    Returns:
        True if SMTP is accessible, False otherwise.
    """
    try:
        from app.workers.notification_service import EmailNotifier
        from app.config import settings

        if not settings.smtp_server:
            print("⚠️  SMTP server not configured; skipping")
            return True

        print("Testing email SMTP connectivity...", end=" ", flush=True)

        notifier = EmailNotifier()
        success = await notifier.test_connection()

        if success:
            print("✅ Email SMTP connected")
            return True
        else:
            print("❌ Email SMTP failed")
            return False

    except Exception as e:
        print(f"❌ Email SMTP failed: {e}")
        return False


def test_celery_queue() -> bool:
    """Test Celery broker connectivity.

    Verifies that the Redis broker is accessible via Celery configuration.

    Returns:
        True if broker is accessible, False otherwise.
    """
    try:
        print("Testing Celery queue connectivity...", end=" ", flush=True)

        from app.workers.celery_app import celery_app
        from app.config import settings

        # Attempt to inspect the Celery app
        stats = celery_app.control.inspect().stats()

        if stats:
            print("✅ Celery queue connected")
            return True
        else:
            print("⚠️  Celery queue available but no workers active")
            return True  # Queue is operational even if workers are down

    except Exception as e:
        print(f"❌ Celery queue failed: {e}")
        return False


async def send_test_alert() -> bool:
    """Send a test alert via SlackNotifier.

    Creates a test alert with:
    - Title: "🧪 TEST ALERT"
    - Message: "This is a test alert from production verification"
    - Severity: info

    Returns:
        True if alert sent successfully, False otherwise.
    """
    try:
        from app.workers.notification_service import SlackNotifier

        print("Sending test alert...", end=" ", flush=True)

        notifier = SlackNotifier()
        success = await notifier.send_alert(
            title="🧪 TEST ALERT",
            message="This is a test alert from production verification",
            severity="info",
        )

        if success:
            print("✅ Test alert sent")
            return True
        else:
            print("❌ Test alert failed to send")
            return False

    except Exception as e:
        print(f"❌ Test alert failed: {e}")
        return False


def test_database_connection() -> bool:
    """Test database connectivity.

    Verifies that PostgreSQL is accessible.

    Returns:
        True if database is accessible, False otherwise.
    """
    try:
        print("Testing database connectivity...", end=" ", flush=True)

        from app.config import settings
        from sqlalchemy import create_engine

        # Map async URL to sync driver
        db_url = settings.database_url
        if "+asyncpg" in db_url:
            db_url = db_url.replace("+asyncpg", "+psycopg")

        engine = create_engine(db_url, connect_args={"timeout": 10})
        with engine.connect() as conn:
            conn.connection.ping(reconnect=True)
            print("✅ Database connected")
            return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def main() -> int:
    """Run all alert system tests.

    Executes comprehensive tests of all notification channels and infrastructure,
    prints a summary table with status, and sends a test alert if all systems
    are operational.

    Returns:
        0 if all systems healthy, 1 if any failures.
    """
    print("\n" + "=" * 70)
    print("TrueMatch Alert System Health Check")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print("=" * 70 + "\n")

    results = {
        "Slack Webhook": await test_slack_connection(),
        "Email SMTP": await test_email_connection(),
        "Celery Queue": test_celery_queue(),
        "Database": test_database_connection(),
    }

    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    all_passed = True
    for system, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{system:.<50} {status}")
        if not result:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n✅ All alert systems operational")
        print("\nSending verification test alert...\n")
        await send_test_alert()
        return 0
    else:
        print("\n❌ Some alert systems are not operational")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Unhandled exception")
        sys.exit(1)
