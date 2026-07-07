#!/usr/bin/env python3
"""
TrueMatch Screenshot Capture Script
Automatically captures all key screenshots for slide deck
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

# Setup
BASE_URL = "http://localhost:3001"
SCREENSHOTS_DIR = Path("/Users/modvader/Documents/codebase/truematch/screenshots")
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Test credentials
ADMIN_EMAIL = "rez@mustafarai.com"
ADMIN_PASSWORD = "Immortal"
RECRUITER_EMAIL = "recruiter@truematch.local"
RECRUITER_PASSWORD = "recruiter123"
CANDIDATE_EMAIL = "candidate@truematch.local"
CANDIDATE_PASSWORD = "candidate123"

def setup_driver():
    """Initialize Chrome driver"""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    return driver

def login(driver, email, password):
    """Login to the platform"""
    driver.get(f"{BASE_URL}/login")
    time.sleep(2)

    # Find and fill email field
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    email_field.clear()
    email_field.send_keys(email)

    # Fill password field
    password_field = driver.find_element(By.NAME, "password")
    password_field.clear()
    password_field.send_keys(password)

    # Click login button
    login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Sign In')]")
    login_button.click()

    # Wait for page to load
    time.sleep(3)

def capture_login_page(driver):
    """Capture login page screenshot"""
    print("📸 Capturing: Login Page")
    driver.get(f"{BASE_URL}/login")
    time.sleep(2)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "01_login_page.png"))
    print("   ✅ Saved: 01_login_page.png")

def capture_admin_dashboard(driver):
    """Capture admin dashboard"""
    print("📸 Capturing: Admin Dashboard")
    login(driver, ADMIN_EMAIL, ADMIN_PASSWORD)
    driver.get(f"{BASE_URL}/admin/dashboard")
    time.sleep(3)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "02_admin_dashboard.png"))
    print("   ✅ Saved: 02_admin_dashboard.png")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Logout') or contains(text(), 'Sign Out')]").click()
    time.sleep(2)

def capture_recruiter_dashboard(driver):
    """Capture recruiter dashboard"""
    print("📸 Capturing: Recruiter Dashboard")
    login(driver, RECRUITER_EMAIL, RECRUITER_PASSWORD)
    driver.get(f"{BASE_URL}/recruiter/dashboard")
    time.sleep(3)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "03_recruiter_dashboard.png"))
    print("   ✅ Saved: 03_recruiter_dashboard.png")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Logout') or contains(text(), 'Sign Out')]").click()
    time.sleep(2)

def capture_candidate_dashboard(driver):
    """Capture candidate dashboard"""
    print("📸 Capturing: Candidate Dashboard")
    login(driver, CANDIDATE_EMAIL, CANDIDATE_PASSWORD)
    driver.get(f"{BASE_URL}/candidate/dashboard")
    time.sleep(3)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "04_candidate_dashboard.png"))
    print("   ✅ Saved: 04_candidate_dashboard.png")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Logout') or contains(text(), 'Sign Out')]").click()
    time.sleep(2)

def capture_chat_interface(driver):
    """Capture chat interface"""
    print("📸 Capturing: Chat Interface")
    login(driver, RECRUITER_EMAIL, RECRUITER_PASSWORD)
    driver.get(f"{BASE_URL}/chat")
    time.sleep(3)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "05_chat_interface.png"))
    print("   ✅ Saved: 05_chat_interface.png")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Logout') or contains(text(), 'Sign Out')]").click()
    time.sleep(2)

def capture_assessment_results(driver):
    """Capture assessment results page"""
    print("📸 Capturing: Assessment Results")
    login(driver, RECRUITER_EMAIL, RECRUITER_PASSWORD)
    # Navigate to a recent assessment (adjust path as needed)
    driver.get(f"{BASE_URL}/recruiter/candidates")
    time.sleep(3)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "06_assessment_results.png"))
    print("   ✅ Saved: 06_assessment_results.png")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Logout') or contains(text(), 'Sign Out')]").click()
    time.sleep(2)

def capture_pipeline_kanban(driver):
    """Capture recruiter pipeline (Kanban view)"""
    print("📸 Capturing: Pipeline Kanban")
    login(driver, RECRUITER_EMAIL, RECRUITER_PASSWORD)
    driver.get(f"{BASE_URL}/recruiter/positions")
    time.sleep(3)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "07_pipeline_kanban.png"))
    print("   ✅ Saved: 07_pipeline_kanban.png")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Logout') or contains(text(), 'Sign Out')]").click()
    time.sleep(2)

def capture_jd_analysis(driver):
    """Capture JD quality analysis"""
    print("📸 Capturing: JD Quality Analysis")
    login(driver, RECRUITER_EMAIL, RECRUITER_PASSWORD)
    driver.get(f"{BASE_URL}/recruiter/jd-simulation")
    time.sleep(3)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "08_jd_analysis.png"))
    print("   ✅ Saved: 08_jd_analysis.png")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Logout') or contains(text(), 'Sign Out')]").click()
    time.sleep(2)

def capture_analytics(driver):
    """Capture admin analytics"""
    print("📸 Capturing: Admin Analytics")
    login(driver, ADMIN_EMAIL, ADMIN_PASSWORD)
    driver.get(f"{BASE_URL}/admin/analytics")
    time.sleep(3)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "09_admin_analytics.png"))
    print("   ✅ Saved: 09_admin_analytics.png")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Logout') or contains(text(), 'Sign Out')]").click()
    time.sleep(2)

def capture_governance_panel(driver):
    """Capture governance review panel"""
    print("📸 Capturing: Governance Review Panel")
    login(driver, ADMIN_EMAIL, ADMIN_PASSWORD)
    driver.get(f"{BASE_URL}/admin/governance-dashboard")
    time.sleep(3)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "10_governance_panel.png"))
    print("   ✅ Saved: 10_governance_panel.png")

def main():
    """Main screenshot capture flow"""
    print("=" * 60)
    print("TrueMatch Screenshot Capture Script")
    print("=" * 60)
    print(f"📁 Saving to: {SCREENSHOTS_DIR}")
    print()

    driver = setup_driver()

    try:
        # Capture all screenshots
        capture_login_page(driver)
        capture_admin_dashboard(driver)
        capture_recruiter_dashboard(driver)
        capture_candidate_dashboard(driver)
        capture_chat_interface(driver)
        capture_assessment_results(driver)
        capture_pipeline_kanban(driver)
        capture_jd_analysis(driver)
        capture_analytics(driver)
        capture_governance_panel(driver)

        print()
        print("=" * 60)
        print("✅ ALL SCREENSHOTS CAPTURED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📁 Location: {SCREENSHOTS_DIR}")
        print()
        print("Screenshots ready for embedding in your slides:")
        for i, file in enumerate(sorted(SCREENSHOTS_DIR.glob("*.png")), 1):
            print(f"   {i}. {file.name}")

    except Exception as e:
        print(f"❌ Error during screenshot capture: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
