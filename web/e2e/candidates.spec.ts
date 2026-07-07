import { test, expect, Page } from '@playwright/test';

/**
 * E2E Tests for Candidate Workflows
 * Tests: Upload resume → Get analysis → Browse jobs → Apply to job
 */

test.describe('Candidate Workflows', () => {
  let page: Page;

  test.beforeEach(async ({ page: p }) => {
    page = p;
    // Navigate to candidate dashboard
    await page.goto('/candidate/dashboard');
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should upload resume and get analysis', async () => {
    // Step 1: Navigate to CV analysis
    await page.click('text=CV Analysis');
    await page.waitForLoadState('networkidle');

    // Step 2: Upload resume file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('tests/fixtures/sample-resume.pdf');

    // Step 3: Wait for analysis to complete
    await page.waitForSelector('[data-testid="analysis-results"]', { timeout: 10000 });

    // Step 4: Verify analysis results display
    const matchScore = await page.locator('[data-testid="match-score"]').textContent();
    expect(matchScore).toBeTruthy();

    const skillsSection = await page.locator('[data-testid="skills-section"]');
    await expect(skillsSection).toBeVisible();
  });

  test('should navigate and filter job listings', async () => {
    // Step 1: Go to job search
    await page.click('text=Browse Jobs');
    await page.waitForLoadState('networkidle');

    // Step 2: Search for jobs
    const searchInput = page.locator('[data-testid="job-search-input"]');
    await searchInput.fill('React Developer');
    await page.keyboard.press('Enter');

    // Step 3: Wait for results
    await page.waitForSelector('[data-testid="job-results"]', { timeout: 5000 });

    // Step 4: Apply filters
    const locationFilter = page.locator('[data-testid="location-filter"]');
    await locationFilter.selectOption('Remote');

    // Step 5: Verify filtered results
    const jobCards = page.locator('[data-testid="job-card"]');
    const count = await jobCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should view job details and match score', async () => {
    // Step 1: Navigate to jobs
    await page.click('text=Browse Jobs');
    await page.waitForLoadState('networkidle');

    // Step 2: Click first job
    const firstJobCard = page.locator('[data-testid="job-card"]').first();
    await firstJobCard.click();

    // Step 3: Verify job detail page
    const jobTitle = page.locator('[data-testid="job-title"]');
    await expect(jobTitle).toBeVisible();

    // Step 4: Check match score gauge
    const matchScore = page.locator('[data-testid="match-score-gauge"]');
    await expect(matchScore).toBeVisible();

    // Step 5: Verify skills radar
    const skillsRadar = page.locator('[data-testid="skills-radar-chart"]');
    await expect(skillsRadar).toBeVisible();
  });

  test('should apply to a job', async () => {
    // Step 1: Navigate to a job
    await page.click('text=Browse Jobs');
    await page.waitForLoadState('networkidle');

    const firstJobCard = page.locator('[data-testid="job-card"]').first();
    await firstJobCard.click();

    // Step 2: Click apply button
    const applyButton = page.locator('button:has-text("Apply Now")');
    await applyButton.click();

    // Step 3: Verify application modal appears
    const modal = page.locator('[data-testid="apply-modal"]');
    await expect(modal).toBeVisible();

    // Step 4: Fill optional cover letter
    const coverLetterTextarea = page.locator('textarea[name="coverLetter"]');
    await coverLetterTextarea.fill('I am excited about this opportunity...');

    // Step 5: Submit application
    const submitButton = page.locator('button:has-text("Submit Application")');
    await submitButton.click();

    // Step 6: Verify success message
    const successMessage = page.locator('[data-testid="success-message"]');
    await expect(successMessage).toBeVisible();
    await expect(successMessage).toContainText('Applied successfully');
  });

  test('should track application status', async () => {
    // Step 1: Navigate to applications
    await page.click('text=My Applications');
    await page.waitForLoadState('networkidle');

    // Step 2: Verify applications list
    const applicationsList = page.locator('[data-testid="applications-list"]');
    await expect(applicationsList).toBeVisible();

    const applicationCards = page.locator('[data-testid="application-card"]');
    const count = await applicationCards.count();
    expect(count).toBeGreaterThan(0);

    // Step 3: Click application to view details
    const firstApplication = applicationCards.first();
    await firstApplication.click();

    // Step 4: Verify application timeline
    const timeline = page.locator('[data-testid="application-timeline"]');
    await expect(timeline).toBeVisible();

    // Step 5: Check for status updates
    const statusElement = page.locator('[data-testid="application-status"]');
    const status = await statusElement.textContent();
    expect(['applied', 'interview', 'offer', 'rejected']).toContain(status?.toLowerCase());
  });

  test('should manage resume versions', async () => {
    // Step 1: Navigate to CV analysis
    await page.click('text=CV Analysis');
    await page.waitForLoadState('networkidle');

    // Step 2: Find resume versions section
    const versionsSection = page.locator('[data-testid="resume-versions"]');
    await expect(versionsSection).toBeVisible();

    // Step 3: Upload new version
    const uploadButton = page.locator('button:has-text("Upload New Version")');
    await uploadButton.click();

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('tests/fixtures/sample-resume-v2.pdf');

    // Step 4: Wait for version to process
    await page.waitForTimeout(2000);

    // Step 5: Verify version appears in list
    const versionsList = page.locator('[data-testid="versions-list"]');
    const versionItems = versionsList.locator('[data-testid="version-item"]');
    const count = await versionItems.count();
    expect(count).toBeGreaterThan(1);
  });

  test('should compare resume versions', async () => {
    // Step 1: Navigate to resume versions
    await page.click('text=CV Analysis');
    await page.waitForLoadState('networkidle');

    const versionsSection = page.locator('[data-testid="resume-versions"]');
    await expect(versionsSection).toBeVisible();

    // Step 2: Select versions to compare
    const compareButton = page.locator('button:has-text("Compare Versions")');
    await compareButton.click();

    // Step 3: Select two versions
    const versionSelects = page.locator('[data-testid="version-select"]');
    const firstSelect = versionSelects.first();
    const secondSelect = versionSelects.nth(1);

    await firstSelect.selectOption('1');
    await secondSelect.selectOption('2');

    // Step 4: View comparison
    const compareButton2 = page.locator('button:has-text("Show Comparison")');
    await compareButton2.click();

    // Step 5: Verify comparison results
    const comparisonResults = page.locator('[data-testid="comparison-results"]');
    await expect(comparisonResults).toBeVisible();

    const differences = page.locator('[data-testid="differences"]');
    await expect(differences).toBeVisible();
  });

  test('should handle pagination in job listings', async () => {
    // Step 1: Navigate to jobs
    await page.click('text=Browse Jobs');
    await page.waitForLoadState('networkidle');

    // Step 2: Scroll to pagination
    const pagination = page.locator('[data-testid="pagination"]');
    await pagination.scrollIntoViewIfNeeded();

    // Step 3: Check next page button
    const nextButton = page.locator('button:has-text("Next")');
    const isEnabled = await nextButton.isEnabled();

    if (isEnabled) {
      // Step 4: Go to next page
      await nextButton.click();
      await page.waitForLoadState('networkidle');

      // Step 5: Verify page updated
      const jobCards = page.locator('[data-testid="job-card"]');
      const count = await jobCards.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  test('should save job to favorites', async () => {
    // Step 1: Navigate to jobs
    await page.click('text=Browse Jobs');
    await page.waitForLoadState('networkidle');

    // Step 2: Click favorite button on first job
    const firstJobCard = page.locator('[data-testid="job-card"]').first();
    const favoriteButton = firstJobCard.locator('[data-testid="favorite-btn"]');
    await favoriteButton.click();

    // Step 3: Verify favorite was saved
    const savedMessage = page.locator('[data-testid="saved-message"]');
    await expect(savedMessage).toBeVisible();

    // Step 4: Navigate to favorites
    await page.click('text=Saved Jobs');
    await page.waitForLoadState('networkidle');

    // Step 5: Verify job appears in favorites
    const savedJobsList = page.locator('[data-testid="saved-jobs-list"]');
    await expect(savedJobsList).toBeVisible();
  });

  test('should complete end-to-end workflow', async () => {
    // Step 1: Upload resume
    await page.click('text=CV Analysis');
    await page.waitForLoadState('networkidle');

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('tests/fixtures/sample-resume.pdf');
    await page.waitForSelector('[data-testid="analysis-results"]');

    // Step 2: Search jobs
    await page.click('text=Browse Jobs');
    const searchInput = page.locator('[data-testid="job-search-input"]');
    await searchInput.fill('Engineer');
    await page.keyboard.press('Enter');
    await page.waitForSelector('[data-testid="job-results"]');

    // Step 3: View job details
    const firstJob = page.locator('[data-testid="job-card"]').first();
    await firstJob.click();
    await expect(page.locator('[data-testid="job-title"]')).toBeVisible();

    // Step 4: Apply to job
    const applyButton = page.locator('button:has-text("Apply Now")');
    await applyButton.click();
    await expect(page.locator('[data-testid="apply-modal"]')).toBeVisible();

    const submitButton = page.locator('button:has-text("Submit Application")');
    await submitButton.click();

    // Step 5: Verify application tracking
    await page.click('text=My Applications');
    await page.waitForLoadState('networkidle');

    const applicationsList = page.locator('[data-testid="applications-list"]');
    await expect(applicationsList).toBeVisible();
  });
});

test.describe('Candidate Error Handling', () => {
  let page: Page;

  test.beforeEach(async ({ page: p }) => {
    page = p;
    await page.goto('/candidate/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should handle resume upload errors', async () => {
    await page.click('text=CV Analysis');
    await page.waitForLoadState('networkidle');

    const fileInput = page.locator('input[type="file"]');

    // Try uploading invalid file type
    await fileInput.setInputFiles({
      name: 'invalid.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('invalid content'),
    });

    const errorMessage = page.locator('[data-testid="error-message"]');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('Invalid');
  });

  test('should handle network errors gracefully', async () => {
    // Simulate offline mode
    await page.context().setOffline(true);

    await page.click('text=Browse Jobs');

    const errorMessage = page.locator('[data-testid="error-message"]');
    await expect(errorMessage).toBeVisible();

    // Restore connection
    await page.context().setOffline(false);
  });

  test('should handle missing required fields in application', async () => {
    await page.click('text=Browse Jobs');
    await page.waitForLoadState('networkidle');

    const firstJob = page.locator('[data-testid="job-card"]').first();
    await firstJob.click();

    const applyButton = page.locator('button:has-text("Apply Now")');
    await applyButton.click();

    const submitButton = page.locator('button:has-text("Submit Application")');
    await submitButton.click();

    const errorMessage = page.locator('[data-testid="validation-error"]');
    await expect(errorMessage).toBeVisible();
  });
});
