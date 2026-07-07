#!/usr/bin/env python3
"""
Automated screenshot capture and save for TrueMatch
Uses Selenium to capture and save all 8 key screenshots
"""

import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configuration
BASE_URL = "http://localhost:3001"
SCREENSHOTS_DIR = Path("/Users/modvader/Documents/codebase/truematch/screenshots")
ADMIN_EMAIL = "rez@mustafarai.com"
ADMIN_PASSWORD = "Immortal"

# Screenshots to capture
SCREENSHOTS = [
    {
        "name": "01_login_page.png",
        "url": "/login",
        "description": "Login Page",
        "login_required": False
    },
    {
        "name": "02_admin_dashboard.png",
        "url": "/admin/dashboard",
        "description": "Admin Dashboard",
        "login_required": True,
        "role": "admin"
    },
    {
        "name": "03_recruiter_dashboard.png",
        "url": "/recruiter/dashboard",
        "description": "Recruiter Dashboard",
        "login_required": True,
        "role": "admin"  # admin can access recruiter dashboard
    },
    {
        "name": "04_candidate_dashboard.png",
        "url": "/candidate/dashboard",
        "description": "Candidate Dashboard",
        "login_required": True,
        "role": "admin"  # admin can access all dashboards
    },
    {
        "name": "05_chat_interface.png",
        "url": "/chat",
        "description": "Chat Interface",
        "login_required": True,
        "role": "admin"
    },
    {
        "name": "06_assessment_results.png",
        "url": "/recruiter/candidates",
        "description": "Assessment Results",
        "login_required": True,
        "role": "admin"
    },
    {
        "name": "07_pipeline_positions.png",
        "url": "/recruiter/positions",
        "description": "Pipeline Positions",
        "login_required": True,
        "role": "admin"
    },
    {
        "name": "08_jd_simulation.png",
        "url": "/recruiter/jd-simulation",
        "description": "JD Simulation",
        "login_required": True,
        "role": "admin"
    }
]

def setup_driver():
    """Initialize Chrome WebDriver"""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    return driver

def login(driver, email, password):
    """Login to the platform"""
    try:
        print("  📝 Logging in...")
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_field.clear()
        email_field.send_keys(email)

        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(password)

        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')]")
        login_button.click()

        # Wait for dashboard to load
        time.sleep(3)
        print("  ✅ Login successful")
        return True
    except Exception as e:
        print(f"  ❌ Login failed: {e}")
        return False

def capture_screenshot(driver, screenshot_info):
    """Capture and save a single screenshot"""
    name = screenshot_info["name"]
    url = screenshot_info["url"]
    description = screenshot_info["description"]
    login_required = screenshot_info.get("login_required", False)

    print(f"\n📸 Capturing: {description}")
    print(f"   URL: {BASE_URL}{url}")

    try:
        # Navigate to page
        driver.get(f"{BASE_URL}{url}")
        time.sleep(3)

        # Save screenshot
        save_path = SCREENSHOTS_DIR / name
        driver.save_screenshot(str(save_path))

        file_size = save_path.stat().st_size
        print(f"   ✅ Saved: {name} ({file_size:,} bytes)")
        return True

    except Exception as e:
        print(f"   ❌ Failed to capture: {e}")
        return False

def main():
    """Main execution"""
    print("=" * 70)
    print("TrueMatch Automated Screenshot Capture")
    print("=" * 70)

    # Create screenshots directory
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Screenshots directory: {SCREENSHOTS_DIR}")

    # Initialize WebDriver
    driver = None
    try:
        driver = setup_driver()
        print("✅ Chrome WebDriver initialized\n")

        # First, capture login page (no login required)
        print("\n--- PUBLIC PAGES ---")
        if not capture_screenshot(driver, SCREENSHOTS[0]):
            print("⚠️  Warning: Login page capture failed")

        # Login once for all authenticated pages
        print("\n--- AUTHENTICATED PAGES ---")
        driver.get(f"{BASE_URL}/login")
        time.sleep(2)

        if not login(driver, ADMIN_EMAIL, ADMIN_PASSWORD):
            print("❌ Failed to login. Cannot capture authenticated pages.")
            return False

        # Capture remaining screenshots
        captured_count = 0
        for screenshot_info in SCREENSHOTS[1:]:
            if capture_screenshot(driver, screenshot_info):
                captured_count += 1

        # Verify all files
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)

        files = sorted(SCREENSHOTS_DIR.glob("*.png"))
        print(f"\n✅ Total files saved: {len(files)}/8")

        if len(files) == 8:
            print("\n🎉 SUCCESS! All 8 screenshots captured and saved!\n")
            for file in files:
                size_kb = file.stat().st_size / 1024
                print(f"  ✓ {file.name} ({size_kb:.1f} KB)")
            return True
        else:
            print(f"\n⚠️  Only {len(files)}/8 files saved")
            print("\nMissing files:")
            saved_names = {f.name for f in files}
            for screenshot in SCREENSHOTS:
                if screenshot["name"] not in saved_names:
                    print(f"  ❌ {screenshot['name']}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            driver.quit()
            print("\n🔌 Chrome WebDriver closed")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
