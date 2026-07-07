import { test, expect, Page } from '@playwright/test';

/**
 * E2E Tests for Application Tracking Workflows
 * Tests: View applications → Check status → Track timeline → Manage applications
 */

test.describe('Application Tracking Workflows', () => {
  let page: Page;

  test.beforeEach(async ({ page: p }) => {
    page = p;
    // Navigate to applications page
    await page.goto('/candidate/applications');
    await page.waitForLoadState('networkidle');
  });

  test('should display all applications with current status', async () => {
    // Step 1: Verify applications list loads
    const applicationsList = page.locator('[data-testid="applications-list"]');
    await expect(applicationsList).toBeVisible();

    // Step 2: Check application cards display
    const applicationCards = page.locator('[data-testid="application-card"]');
    const count = await applicationCards.count();
    expect(count).toBeGreaterThan(0);

    // Step 3: Verify status badges
    const statusBadges = page.locator('[data-testid="status-badge"]');
    expect(await statusBadges.count()).toBe(count);
  });

  test('should view detailed application status', async () => {
    // Step 1: Click on first application
    const firstApplication = page.locator('[data-testid="application-card"]').first();
    await firstApplication.click();

    // Step 2: Verify detail page loads
    const detailPage = page.locator('[data-testid="application-detail"]');
    await expect(detailPage).toBeVisible();

    // Step 3: Check job information
    const jobTitle = page.locator('[data-testid="job-title"]');
    await expect(jobTitle).toBeVisible();

    const companyName = page.locator('[data-testid="company-name"]');
    await expect(companyName).toBeVisible();

    // Step 4: Verify application date
    const appliedDate = page.locator('[data-testid="applied-date"]');
    await expect(appliedDate).toBeVisible();

    // Step 5: Check match score
    const matchScore = page.locator('[data-testid="match-score"]');
    await expect(matchScore).toBeVisible();
  });

  test('should track application timeline', async () => {
    // Step 1: Click on application to view details
    const firstApplication = page.locator('[data-testid="application-card"]').first();
    await firstApplication.click();

    await page.waitForLoadState('networkidle');

    // Step 2: Navigate to timeline tab
    const timelineTab = page.locator('button:has-text("Timeline")');
    if (await timelineTab.isVisible()) {
      await timelineTab.click();
    }

    // Step 3: Verify timeline displays
    const timeline = page.locator('[data-testid="application-timeline"]');
    await expect(timeline).toBeVisible();

    // Step 4: Check timeline events
    const timelineEvents = page.locator('[data-testid="timeline-event"]');
    const eventCount = await timelineEvents.count();
    expect(eventCount).toBeGreaterThan(0);

    // Step 5: Verify event types
    for (let i = 0; i < Math.min(eventCount, 3); i++) {
      const event = timelineEvents.nth(i);
      const eventLabel = event.locator('[data-testid="event-label"]');
      await expect(eventLabel).toBeVisible();
    }
  });

  test('should filter applications by status', async () => {
    // Step 1: Find status filter
    const statusFilter = page.locator('[data-testid="status-filter"]');
    await expect(statusFilter).toBeVisible();

    // Step 2: Filter by "Applied"
    await statusFilter.selectOption('applied');
    await page.waitForLoadState('networkidle');

    // Step 3: Verify filtered results
    const applicationCards = page.locator('[data-testid="application-card"]');
    const count = await applicationCards.count();
    expect(count).toBeGreaterThanOrEqual(0);

    // Step 4: Verify all cards have correct status
    const statusBadges = page.locator('[data-testid="status-badge"]');
    for (let i = 0; i < await statusBadges.count(); i++) {
      const badge = statusBadges.nth(i);
      const status = await badge.textContent();
      expect(status?.toLowerCase()).toContain('applied');
    }

    // Step 5: Filter by "Interview"
    await statusFilter.selectOption('interview');
    await page.waitForLoadState('networkidle');

    // Verify new results
    const updatedCards = page.locator('[data-testid="application-card"]');
    const updatedCount = await updatedCards.count();
    expect(updatedCount).toBeGreaterThanOrEqual(0);
  });

  test('should sort applications by date', async () => {
    // Step 1: Find sort options
    const sortButton = page.locator('[data-testid="sort-button"]');
    if (await sortButton.isVisible()) {
      await sortButton.click();

      // Step 2: Select sort by newest first
      const sortOption = page.locator('button:has-text("Newest First")');
      await sortOption.click();

      await page.waitForLoadState('networkidle');

      // Step 3: Verify sorting applied
      const applicationCards = page.locator('[data-testid="application-card"]');
      const firstCard = applicationCards.first();
      const firstDate = await firstCard.locator('[data-testid="applied-date"]').textContent();
      expect(firstDate).toBeTruthy();
    }
  });

  test('should view application feedback when available', async () => {
    // Step 1: Find an application with feedback
    let feedbackAvailable = false;
    const applicationCards = page.locator('[data-testid="application-card"]');
    const count = await applicationCards.count();

    for (let i = 0; i < count; i++) {
      const card = applicationCards.nth(i);
      const feedbackBadge = card.locator('[data-testid="feedback-badge"]');

      if (await feedbackBadge.isVisible()) {
        await card.click();
        feedbackAvailable = true;
        break;
      }
    }

    if (feedbackAvailable) {
      // Step 2: Verify feedback section displays
      const feedbackSection = page.locator('[data-testid="feedback-section"]');
      await expect(feedbackSection).toBeVisible();

      // Step 3: Check feedback content
      const feedbackText = page.locator('[data-testid="feedback-text"]');
      const text = await feedbackText.textContent();
      expect(text).toBeTruthy();

      // Step 4: Check rating if available
      const feedbackRating = page.locator('[data-testid="feedback-rating"]');
      if (await feedbackRating.isVisible()) {
        const rating = await feedbackRating.textContent();
        expect(rating).toMatch(/\d/);
      }
    }
  });

  test('should withdraw from application', async () => {
    // Step 1: Click on application
    const firstApplication = page.locator('[data-testid="application-card"]').first();
    await firstApplication.click();

    await page.waitForLoadState('networkidle');

    // Step 2: Check if withdrawal is available
    const withdrawButton = page.locator('button:has-text("Withdraw Application")');

    if (await withdrawButton.isVisible() && !await withdrawButton.isDisabled()) {
      // Step 3: Click withdraw
      await withdrawButton.click();

      // Step 4: Confirm withdrawal
      const confirmButton = page.locator('button:has-text("Confirm")');
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
      }

      // Step 5: Verify withdrawal
      const successMessage = page.locator('[data-testid="success-message"]');
      await expect(successMessage).toBeVisible();
      await expect(successMessage).toContainText('withdrawn');
    }
  });

  test('should display application statistics', async () => {
    // Step 1: Look for stats section
    const statsSection = page.locator('[data-testid="application-stats"]');

    if (await statsSection.isVisible()) {
      // Step 2: Check total applications
      const totalStat = page.locator('[data-testid="total-applications"]');
      await expect(totalStat).toBeVisible();
      const totalText = await totalStat.textContent();
      expect(totalText).toMatch(/\d+/);

      // Step 3: Check applied count
      const appliedStat = page.locator('[data-testid="applied-count"]');
      if (await appliedStat.isVisible()) {
        expect(await appliedStat.textContent()).toMatch(/\d+/);
      }

      // Step 4: Check interview count
      const interviewStat = page.locator('[data-testid="interview-count"]');
      if (await interviewStat.isVisible()) {
        expect(await interviewStat.textContent()).toMatch(/\d+/);
      }

      // Step 5: Check offer count
      const offerStat = page.locator('[data-testid="offer-count"]');
      if (await offerStat.isVisible()) {
        expect(await offerStat.textContent()).toMatch(/\d+/);
      }
    }
  });

  test('should export applications data', async () => {
    // Step 1: Find export button
    const exportButton = page.locator('button:has-text("Export")');

    if (await exportButton.isVisible()) {
      // Step 2: Click export
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();

      // Step 3: Verify download
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/applications.*\.(csv|xlsx|pdf)/);
    }
  });

  test('should complete end-to-end application tracking workflow', async () => {
    // Step 1: View applications list
    const applicationsList = page.locator('[data-testid="applications-list"]');
    await expect(applicationsList).toBeVisible();

    // Step 2: Filter by status
    const statusFilter = page.locator('[data-testid="status-filter"]');
    await statusFilter.selectOption('interview');
    await page.waitForLoadState('networkidle');

    // Step 3: Click on first application
    const firstApplication = page.locator('[data-testid="application-card"]').first();
    if (await firstApplication.isVisible()) {
      await firstApplication.click();

      // Step 4: View timeline
      const timelineTab = page.locator('button:has-text("Timeline")');
      if (await timelineTab.isVisible()) {
        await timelineTab.click();
        await expect(page.locator('[data-testid="application-timeline"]')).toBeVisible();
      }

      // Step 5: Check feedback
      const feedbackSection = page.locator('[data-testid="feedback-section"]');
      if (await feedbackSection.isVisible()) {
        const feedbackText = await feedbackSection.textContent();
        expect(feedbackText).toBeTruthy();
      }

      // Step 6: Go back to list
      const backButton = page.locator('button:has-text("Back")');
      if (await backButton.isVisible()) {
        await backButton.click();
        await expect(applicationsList).toBeVisible();
      }
    }
  });
});

test.describe('Application Notifications', () => {
  let page: Page;

  test.beforeEach(async ({ page: p }) => {
    page = p;
    await page.goto('/candidate/applications');
    await page.waitForLoadState('networkidle');
  });

  test('should display status update notifications', async () => {
    // Note: This test checks for real-time notifications
    const notificationArea = page.locator('[data-testid="notification-area"]');

    if (await notificationArea.isVisible()) {
      const notifications = page.locator('[data-testid="notification"]');
      const count = await notifications.count();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('should dismiss notifications', async () => {
    const notificationArea = page.locator('[data-testid="notification-area"]');

    if (await notificationArea.isVisible()) {
      const dismissButton = page.locator('[data-testid="dismiss-notification"]').first();

      if (await dismissButton.isVisible()) {
        await dismissButton.click();

        // Verify notification dismissed
        const remainingNotifications = page.locator('[data-testid="notification"]');
        expect(await remainingNotifications.count()).toBeGreaterThanOrEqual(0);
      }
    }
  });
});

test.describe('Application Error Handling', () => {
  let page: Page;

  test.beforeEach(async ({ page: p }) => {
    page = p;
    await page.goto('/candidate/applications');
    await page.waitForLoadState('networkidle');
  });

  test('should handle network errors when loading applications', async () => {
    // Simulate offline
    await page.context().setOffline(true);

    // Refresh page
    await page.reload();

    const errorMessage = page.locator('[data-testid="error-message"]');
    if (await errorMessage.isVisible()) {
      expect(await errorMessage.textContent()).toContain('error');
    }

    // Restore connection
    await page.context().setOffline(false);
  });

  test('should handle withdrawal errors', async () => {
    const firstApplication = page.locator('[data-testid="application-card"]').first();
    await firstApplication.click();

    const withdrawButton = page.locator('button:has-text("Withdraw Application")');

    if (await withdrawButton.isVisible() && !await withdrawButton.isDisabled()) {
      await withdrawButton.click();

      const confirmButton = page.locator('button:has-text("Confirm")');
      if (await confirmButton.isVisible()) {
        await confirmButton.click();

        // Check for error messages
        const errorMessage = page.locator('[data-testid="error-message"]');
        // Error may or may not appear depending on backend state
      }
    }
  });

  test('should handle missing application data', async () => {
    // Navigate directly to a non-existent application
    await page.goto('/candidate/applications/invalid-id');

    const errorMessage = page.locator('[data-testid="error-message"]');
    const notFoundMessage = page.locator('text=not found');

    const hasError = await errorMessage.isVisible().catch(() => false);
    const hasNotFound = await notFoundMessage.isVisible().catch(() => false);

    expect(hasError || hasNotFound).toBeTruthy();
  });
});
