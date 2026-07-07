/**
 * E2E TEST: Resume Upload → Analysis → Application
 *
 * This test covers the critical user flow where a candidate:
 * 1. Uploads a resume file
 * 2. Views CV analysis
 * 3. Matches with job opportunities
 * 4. Applies to jobs
 */

import { test, expect } from '@playwright/test';

test.describe('Resume Upload & Application Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the candidate dashboard
    await page.goto('/candidate/dashboard');

    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should upload resume and view analysis', async ({ page }) => {
    // Navigate to resume upload section
    await page.click('[data-testid="upload-resume-button"]');

    // Wait for upload modal to appear
    await expect(page.locator('[data-testid="resume-upload-modal"]')).toBeVisible();

    // Upload a test resume file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-fixtures/sample-resume.pdf');

    // Click upload button
    await page.click('[data-testid="upload-submit-button"]');

    // Wait for upload to complete
    await expect(page.locator('[data-testid="upload-success-message"]')).toBeVisible();

    // Close modal
    await page.click('[data-testid="modal-close-button"]');

    // Verify resume appears in the list
    await expect(page.locator('text=sample-resume.pdf')).toBeVisible();
  });

  test('should display resume analysis', async ({ page }) => {
    // Click on a resume to view analysis
    await page.click('[data-testid="resume-item"]');

    // Wait for analysis to load
    await page.waitForSelector('[data-testid="resume-analysis-panel"]');

    // Verify analysis sections are displayed
    await expect(page.locator('[data-testid="skills-section"]')).toBeVisible();
    await expect(page.locator('[data-testid="experience-section"]')).toBeVisible();
    await expect(page.locator('[data-testid="education-section"]')).toBeVisible();

    // Check that skills are extracted
    const skillsList = page.locator('[data-testid="skills-list"]');
    const skillCount = await skillsList.locator('li').count();
    expect(skillCount).toBeGreaterThan(0);
  });

  test('should show job matches', async ({ page }) => {
    // Navigate to resume
    await page.click('[data-testid="resume-item"]');

    // Click on "Matching Jobs" tab
    await page.click('[data-testid="matching-jobs-tab"]');

    // Wait for jobs to load
    await page.waitForSelector('[data-testid="job-card"]');

    // Verify job cards are displayed
    const jobCards = page.locator('[data-testid="job-card"]');
    await expect(jobCards.first()).toBeVisible();

    // Check match score is displayed
    await expect(jobCards.first().locator('[data-testid="match-score"]')).toBeVisible();
  });

  test('should apply to a job', async ({ page }) => {
    // Navigate to matching jobs
    await page.click('[data-testid="resume-item"]');
    await page.click('[data-testid="matching-jobs-tab"]');

    // Wait for jobs to load
    await page.waitForSelector('[data-testid="job-card"]');

    // Click apply button on first job
    await page.click('[data-testid="job-card"] [data-testid="apply-button"]');

    // Verify application modal appears
    await expect(page.locator('[data-testid="application-modal"]')).toBeVisible();

    // Fill in application form if needed
    const coverLetterField = page.locator('[data-testid="cover-letter-input"]');
    if (await coverLetterField.isVisible()) {
      await coverLetterField.fill('I am interested in this position because...');
    }

    // Submit application
    await page.click('[data-testid="submit-application-button"]');

    // Verify success message
    await expect(page.locator('[data-testid="application-success-message"]')).toBeVisible();
  });

  test('should show application in applications list', async ({ page }) => {
    // Navigate to Applications page
    await page.goto('/candidate/applications');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify applications are displayed
    const applicationCards = page.locator('[data-testid="application-card"]');
    await expect(applicationCards.first()).toBeVisible();

    // Check that application status is shown
    await expect(
      applicationCards.first().locator('[data-testid="application-status"]')
    ).toBeVisible();
  });

  test('should handle file upload errors gracefully', async ({ page }) => {
    // Open upload modal
    await page.click('[data-testid="upload-resume-button"]');

    // Try to upload invalid file type
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-fixtures/invalid-file.txt');

    // Submit upload
    await page.click('[data-testid="upload-submit-button"]');

    // Verify error message
    await expect(page.locator('[data-testid="upload-error-message"]')).toBeVisible();
    expect(
      await page.locator('[data-testid="upload-error-message"]').textContent()
    ).toContain('PDF');
  });

  test('should show loading states during operations', async ({ page }) => {
    // Open upload modal
    await page.click('[data-testid="upload-resume-button"]');

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-fixtures/sample-resume.pdf');

    // Submit upload - should show loading
    await page.click('[data-testid="upload-submit-button"]');

    // Verify loading indicator appears
    await expect(page.locator('[role="progressbar"]')).toBeVisible();

    // Wait for loading to complete
    await page.waitForSelector('[data-testid="upload-success-message"]');

    // Verify loading indicator is gone
    await expect(page.locator('[role="progressbar"]')).not.toBeVisible();
  });

  test('should maintain state on page refresh', async ({ page }) => {
    // Upload a resume
    await page.click('[data-testid="upload-resume-button"]');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-fixtures/sample-resume.pdf');
    await page.click('[data-testid="upload-submit-button"]');
    await expect(page.locator('[data-testid="upload-success-message"]')).toBeVisible();

    // Get the resume ID for verification
    const resumeId = await page.locator('[data-testid="resume-item"]').getAttribute('data-resume-id');

    // Refresh page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify resume is still visible
    await expect(page.locator(`[data-resume-id="${resumeId}"]`)).toBeVisible();
  });

  test('should be accessible', async ({ page }) => {
    // Upload button should be accessible
    const uploadButton = page.locator('[data-testid="upload-resume-button"]');
    await expect(uploadButton).toHaveAccessibleName();

    // Open modal
    await uploadButton.click();

    // Modal should have proper ARIA attributes
    const modal = page.locator('[data-testid="resume-upload-modal"]');
    await expect(modal).toHaveAttribute('role', 'dialog');

    // Close button should be accessible
    const closeButton = page.locator('[data-testid="modal-close-button"]');
    await expect(closeButton).toHaveAccessibleName();

    // Can navigate with keyboard
    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible();
  });
});

test.describe('Resume Upload Mobile Flow', () => {
  test.use({
    viewport: { width: 375, height: 812 }, // iPhone 12 size
  });

  test('should work on mobile devices', async ({ page }) => {
    await page.goto('/candidate/dashboard');

    // Upload button should be visible on mobile
    await expect(page.locator('[data-testid="upload-resume-button"]')).toBeVisible();

    // Open upload modal
    await page.click('[data-testid="upload-resume-button"]');

    // Modal should be full-width on mobile
    const modal = page.locator('[data-testid="resume-upload-modal"]');
    const boundingBox = await modal.boundingBox();
    expect(boundingBox?.width).toBeLessThanOrEqual(375);
  });
});
