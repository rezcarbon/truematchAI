/**
 * E2E TEST: Create JD → Optimize → Simulate
 *
 * This test covers the recruiter flow where they:
 * 1. Create/input a job description
 * 2. Optimize it using AI
 * 3. Run simulations to predict candidate matches
 * 4. Track matched candidates
 */

import { test, expect } from '@playwright/test';

test.describe('JD Optimizer & Simulation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to recruiter dashboard
    await page.goto('/recruiter/dashboard');

    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should access JD optimizer', async ({ page }) => {
    // Click on JD Optimizer in navigation
    await page.click('[data-testid="nav-jd-optimizer"]');

    // Verify JD optimizer page loads
    await expect(page.locator('[data-testid="jd-optimizer-container"]')).toBeVisible();

    // Verify main sections are present
    await expect(page.locator('[data-testid="jd-input-section"]')).toBeVisible();
    await expect(page.locator('[data-testid="jd-output-section"]')).toBeVisible();
  });

  test('should input and optimize job description', async ({ page }) => {
    // Navigate to JD optimizer
    await page.goto('/recruiter/jd-optimizer');

    // Find JD input textarea
    const jdInput = page.locator('[data-testid="jd-textarea"]');
    await expect(jdInput).toBeVisible();

    // Enter a job description
    const jobDescription = `
      We are looking for a Senior Software Engineer with 5+ years of experience.
      Requirements:
      - React and TypeScript expertise
      - Node.js backend experience
      - AWS knowledge
      - Team collaboration skills
    `;

    await jdInput.fill(jobDescription);

    // Click optimize button
    await page.click('[data-testid="optimize-button"]');

    // Wait for optimization to complete
    await page.waitForSelector('[data-testid="optimization-results"]');

    // Verify optimized JD is displayed
    const optimizedOutput = page.locator('[data-testid="optimized-jd-output"]');
    await expect(optimizedOutput).toBeVisible();

    // Verify improvements are listed
    const improvementsList = page.locator('[data-testid="improvements-list"]');
    const improvementItems = improvementsList.locator('li');
    expect(await improvementItems.count()).toBeGreaterThan(0);
  });

  test('should show match predictions', async ({ page }) => {
    // Navigate to JD optimizer
    await page.goto('/recruiter/jd-optimizer');

    // Input and optimize JD
    const jdInput = page.locator('[data-testid="jd-textarea"]');
    await jdInput.fill('Senior React Developer needed');

    await page.click('[data-testid="optimize-button"]');

    // Wait for results
    await page.waitForSelector('[data-testid="match-predictions"]');

    // Verify predictions section is visible
    const predictions = page.locator('[data-testid="match-predictions"]');
    await expect(predictions).toBeVisible();

    // Check that predicted matches are shown
    const matchCards = predictions.locator('[data-testid="match-card"]');
    expect(await matchCards.count()).toBeGreaterThan(0);

    // Verify each match has a score
    for (let i = 0; i < Math.min(3, await matchCards.count()); i++) {
      const card = matchCards.nth(i);
      await expect(card.locator('[data-testid="match-percentage"]')).toBeVisible();
    }
  });

  test('should run simulation', async ({ page }) => {
    // Navigate to JD optimizer
    await page.goto('/recruiter/jd-optimizer');

    // Input JD and optimize
    const jdInput = page.locator('[data-testid="jd-textarea"]');
    await jdInput.fill('Full Stack Developer - React & Node.js');

    await page.click('[data-testid="optimize-button"]');
    await page.waitForSelector('[data-testid="optimization-results"]');

    // Click Run Simulation button
    await page.click('[data-testid="run-simulation-button"]');

    // Verify simulation starts and shows loading
    await expect(page.locator('[data-testid="simulation-loading"]')).toBeVisible();

    // Wait for simulation to complete
    await page.waitForSelector('[data-testid="simulation-results"]', { timeout: 30000 });

    // Verify results are displayed
    const results = page.locator('[data-testid="simulation-results"]');
    await expect(results).toBeVisible();

    // Check for key metrics
    await expect(results.locator('[data-testid="total-matches"]')).toBeVisible();
    await expect(results.locator('[data-testid="average-match-score"]')).toBeVisible();
  });

  test('should display matched candidates', async ({ page }) => {
    // Navigate to JD optimizer
    await page.goto('/recruiter/jd-optimizer');

    // Run through optimization and simulation
    const jdInput = page.locator('[data-testid="jd-textarea"]');
    await jdInput.fill('Senior DevOps Engineer');

    await page.click('[data-testid="optimize-button"]');
    await page.waitForSelector('[data-testid="optimization-results"]');

    await page.click('[data-testid="run-simulation-button"]');
    await page.waitForSelector('[data-testid="simulation-results"]');

    // Navigate to matched candidates section
    await page.click('[data-testid="matched-candidates-tab"]');

    // Wait for candidates to load
    await page.waitForSelector('[data-testid="candidate-card"]');

    // Verify candidate cards are displayed
    const candidateCards = page.locator('[data-testid="candidate-card"]');
    expect(await candidateCards.count()).toBeGreaterThan(0);

    // Check candidate card content
    const firstCard = candidateCards.first();
    await expect(firstCard.locator('[data-testid="candidate-name"]')).toBeVisible();
    await expect(firstCard.locator('[data-testid="match-percentage"]')).toBeVisible();
    await expect(firstCard.locator('[data-testid="skills-list"]')).toBeVisible();
  });

  test('should allow batch actions on candidates', async ({ page }) => {
    // Navigate to matched candidates
    await page.goto('/recruiter/jd-optimizer');

    const jdInput = page.locator('[data-testid="jd-textarea"]');
    await jdInput.fill('Backend Engineer');

    await page.click('[data-testid="optimize-button"]');
    await page.waitForSelector('[data-testid="optimization-results"]');

    await page.click('[data-testid="run-simulation-button"]');
    await page.waitForSelector('[data-testid="simulation-results"]');

    await page.click('[data-testid="matched-candidates-tab"]');
    await page.waitForSelector('[data-testid="candidate-card"]');

    // Select multiple candidates
    const checkboxes = page.locator('[data-testid="candidate-checkbox"]');
    const firstCheckbox = checkboxes.first();
    await firstCheckbox.click();

    // Get the number of selected
    const selectedCount = await page.locator('[data-testid="selected-count"]').textContent();
    expect(selectedCount).toContain('1');

    // Click second checkbox if available
    if ((await checkboxes.count()) > 1) {
      await checkboxes.nth(1).click();
      const updatedCount = await page.locator('[data-testid="selected-count"]').textContent();
      expect(updatedCount).toContain('2');
    }

    // Verify batch action buttons appear
    await expect(page.locator('[data-testid="batch-action-buttons"]')).toBeVisible();
  });

  test('should save JD for reuse', async ({ page }) => {
    // Navigate to JD optimizer
    await page.goto('/recruiter/jd-optimizer');

    // Input and optimize JD
    const jdInput = page.locator('[data-testid="jd-textarea"]');
    const jdContent = 'Architect - Cloud Infrastructure';
    await jdInput.fill(jdContent);

    await page.click('[data-testid="optimize-button"]');
    await page.waitForSelector('[data-testid="optimization-results"]');

    // Click Save JD button
    await page.click('[data-testid="save-jd-button"]');

    // Verify save dialog appears
    await expect(page.locator('[data-testid="save-jd-dialog"]')).toBeVisible();

    // Enter a name
    const nameInput = page.locator('[data-testid="jd-name-input"]');
    await nameInput.fill('Cloud Architect Position');

    // Save
    await page.click('[data-testid="save-confirm-button"]');

    // Verify success message
    await expect(page.locator('[data-testid="save-success-message"]')).toBeVisible();
  });

  test('should load saved JDs', async ({ page }) => {
    // Navigate to JD optimizer
    await page.goto('/recruiter/jd-optimizer');

    // Check if there's a Load JD section
    const loadButton = page.locator('[data-testid="load-jd-button"]');
    if (await loadButton.isVisible()) {
      await loadButton.click();

      // Verify list of saved JDs appears
      await expect(page.locator('[data-testid="saved-jds-list"]')).toBeVisible();

      const savedJDs = page.locator('[data-testid="saved-jd-item"]');
      if (await savedJDs.count() > 0) {
        // Click first saved JD
        await savedJDs.first().click();

        // Verify it loads into the textarea
        const jdInput = page.locator('[data-testid="jd-textarea"]');
        const content = await jdInput.inputValue();
        expect(content.length).toBeGreaterThan(0);
      }
    }
  });

  test('should show optimization metrics', async ({ page }) => {
    // Navigate to JD optimizer
    await page.goto('/recruiter/jd-optimizer');

    // Input JD
    const jdInput = page.locator('[data-testid="jd-textarea"]');
    await jdInput.fill('Looking for experienced Full Stack Developer');

    // Click optimize
    await page.click('[data-testid="optimize-button"]');
    await page.waitForSelector('[data-testid="optimization-results"]');

    // Verify metrics are displayed
    const metrics = page.locator('[data-testid="optimization-metrics"]');
    await expect(metrics).toBeVisible();

    // Check for specific metrics
    await expect(metrics.locator('[data-testid="clarity-score"]')).toBeVisible();
    await expect(metrics.locator('[data-testid="keyword-coverage"]')).toBeVisible();
    await expect(metrics.locator('[data-testid="competition-level"]')).toBeVisible();
  });

  test('should handle empty JD submission', async ({ page }) => {
    // Navigate to JD optimizer
    await page.goto('/recruiter/jd-optimizer');

    // Try to optimize empty JD
    const optimizeButton = page.locator('[data-testid="optimize-button"]');

    // Button should be disabled or show error
    const isDisabled = await optimizeButton.isDisabled();
    if (!isDisabled) {
      await optimizeButton.click();
      // Should show validation error
      await expect(page.locator('[data-testid="validation-error"]')).toBeVisible();
    }
  });

  test('should be accessible', async ({ page }) => {
    // Navigate to JD optimizer
    await page.goto('/recruiter/jd-optimizer');

    // Main heading should exist
    await expect(page.locator('h1, h2').first()).toBeVisible();

    // Optimize button should be accessible
    const optimizeButton = page.locator('[data-testid="optimize-button"]');
    await expect(optimizeButton).toHaveAccessibleName();

    // Textarea should have label
    const jdTextarea = page.locator('[data-testid="jd-textarea"]');
    const label = page.locator('label[for="jd-textarea"]');
    if (await label.isVisible()) {
      await expect(label).toHaveText(/job description|jd/i);
    }
  });
});

test.describe('JD Optimizer Mobile Flow', () => {
  test.use({
    viewport: { width: 375, height: 812 }, // iPhone 12 size
  });

  test('should work on mobile devices', async ({ page }) => {
    await page.goto('/recruiter/jd-optimizer');

    // Layout should be responsive
    const container = page.locator('[data-testid="jd-optimizer-container"]');
    const boundingBox = await container.boundingBox();
    expect(boundingBox?.width).toBeLessThanOrEqual(375);

    // All buttons should be accessible
    await expect(page.locator('[data-testid="optimize-button"]')).toBeVisible();
  });
});
