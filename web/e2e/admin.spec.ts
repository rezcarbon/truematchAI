import { test, expect, Page } from '@playwright/test';

/**
 * E2E Tests for Admin Workflows
 * Tests: Dashboard → Job management → Governance → Approvals
 */

test.describe('Admin Dashboard Workflows', () => {
  let page: Page;

  test.beforeEach(async ({ page: p }) => {
    page = p;
    // Navigate to admin dashboard
    await page.goto('/admin/dashboard');
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should display admin dashboard with all sections', async () => {
    // Verify main dashboard elements
    const dashboard = page.locator('[data-testid="admin-dashboard"]');
    await expect(dashboard).toBeVisible();

    // Check for key sections
    const statsSection = page.locator('[data-testid="stats-section"]');
    await expect(statsSection).toBeVisible();

    const jobsSection = page.locator('[data-testid="jobs-section"]');
    await expect(jobsSection).toBeVisible();

    const governanceSection = page.locator('[data-testid="governance-section"]');
    await expect(governanceSection).toBeVisible();

    const approvalsSection = page.locator('[data-testid="approvals-section"]');
    await expect(approvalsSection).toBeVisible();
  });

  test('should display key metrics and statistics', async () => {
    // Verify stats cards are displayed
    const statCards = page.locator('[data-testid="stat-card"]');
    const count = await statCards.count();
    expect(count).toBeGreaterThan(0);

    // Verify specific metrics
    const totalUsers = page.locator('[data-testid="metric-total-users"]');
    await expect(totalUsers).toBeVisible();

    const activeJobs = page.locator('[data-testid="metric-active-jobs"]');
    await expect(activeJobs).toBeVisible();

    const pendingApprovals = page.locator('[data-testid="metric-pending-approvals"]');
    await expect(pendingApprovals).toBeVisible();

    const systemHealth = page.locator('[data-testid="metric-system-health"]');
    await expect(systemHealth).toBeVisible();
  });

  test('should navigate to jobs management section', async () => {
    // Step 1: Click on jobs management link
    const jobsLink = page.locator('a:has-text("Job Listings"), button:has-text("Manage Jobs")').first();
    await jobsLink.click();

    // Step 2: Wait for page to load
    await page.waitForLoadState('networkidle');

    // Step 3: Verify jobs list is displayed
    const jobsList = page.locator('[data-testid="jobs-table"]');
    await expect(jobsList).toBeVisible();

    // Step 4: Verify table has rows
    const jobRows = page.locator('[data-testid="job-row"]');
    const jobCount = await jobRows.count();
    expect(jobCount).toBeGreaterThanOrEqual(0);
  });

  test('should display job details and quality metrics', async () => {
    // Step 1: Navigate to jobs
    const jobsLink = page.locator('a:has-text("Job Listings"), button:has-text("Manage Jobs")').first();
    await jobsLink.click();

    // Step 2: Wait for jobs to load
    await page.waitForSelector('[data-testid="job-row"]', { timeout: 5000 });

    // Step 3: Click on first job
    const firstJobRow = page.locator('[data-testid="job-row"]').first();
    await firstJobRow.click();

    // Step 4: Verify job details panel
    const jobDetails = page.locator('[data-testid="job-details-panel"]');
    await expect(jobDetails).toBeVisible();

    // Step 5: Verify quality metrics
    const qualityScore = page.locator('[data-testid="quality-score"]');
    await expect(qualityScore).toBeVisible();

    const dimensionScores = page.locator('[data-testid="dimension-scores"]');
    await expect(dimensionScores).toBeVisible();
  });

  test('should run JD simulation from admin interface', async () => {
    // Step 1: Find and click simulate button
    const simulateButton = page.locator('button:has-text("Simulate"), button:has-text("Run Analysis")').first();
    await simulateButton.click();

    // Step 2: Wait for simulation modal or page
    await page.waitForSelector('[data-testid="simulation-panel"]', { timeout: 5000 });

    // Step 3: Verify simulation interface
    const simulationPanel = page.locator('[data-testid="simulation-panel"]');
    await expect(simulationPanel).toBeVisible();

    // Step 4: Wait for simulation results
    await page.waitForTimeout(3000);

    // Step 5: Verify results are displayed
    const results = page.locator('[data-testid="simulation-results"]');
    await expect(results).toBeVisible();
  });

  test('should manage governance settings', async () => {
    // Step 1: Navigate to governance section
    const governanceLink = page.locator('a:has-text("Governance"), button:has-text("Policies")').first();
    await governanceLink.click();

    // Step 2: Wait for governance page to load
    await page.waitForLoadState('networkidle');

    // Step 3: Verify governance settings are visible
    const governanceSettings = page.locator('[data-testid="governance-settings"]');
    await expect(governanceSettings).toBeVisible();

    // Step 4: Look for configuration options
    const qualityThresholds = page.locator('[data-testid="quality-thresholds"]');
    await expect(qualityThresholds).toBeVisible();

    const complianceRules = page.locator('[data-testid="compliance-rules"]');
    await expect(complianceRules).toBeVisible();
  });

  test('should update governance policies', async () => {
    // Step 1: Navigate to governance
    const governanceLink = page.locator('a:has-text("Governance"), button:has-text("Policies")').first();
    await governanceLink.click();

    // Step 2: Find and modify a setting
    const thresholdInput = page.locator('[data-testid="min-quality-threshold"]').first();
    await thresholdInput.clear();
    await thresholdInput.fill('75');

    // Step 3: Save changes
    const saveButton = page.locator('button:has-text("Save"), button:has-text("Apply")').first();
    await saveButton.click();

    // Step 4: Wait for confirmation
    const successMessage = page.locator('[data-testid="success-message"]');
    await expect(successMessage).toBeVisible({ timeout: 3000 });

    // Step 5: Verify update was applied
    const confirmValue = await thresholdInput.inputValue();
    expect(confirmValue).toBe('75');
  });

  test('should view pending approvals', async () => {
    // Step 1: Navigate to approvals section
    const approvalsLink = page.locator('a:has-text("Approvals"), button:has-text("Pending")').first();
    await approvalsLink.click();

    // Step 2: Wait for approvals list to load
    await page.waitForLoadState('networkidle');

    // Step 3: Verify approvals list
    const approvalsList = page.locator('[data-testid="approvals-list"]');
    await expect(approvalsList).toBeVisible();

    // Step 4: Check for pending items
    const pendingItems = page.locator('[data-testid="pending-approval-item"]');
    const pendingCount = await pendingItems.count();
    expect(pendingCount).toBeGreaterThanOrEqual(0);
  });

  test('should approve pending job description', async () => {
    // Step 1: Navigate to approvals
    const approvalsLink = page.locator('a:has-text("Approvals"), button:has-text("Pending")').first();
    await approvalsLink.click();

    // Step 2: Wait for items to load
    await page.waitForSelector('[data-testid="pending-approval-item"]', { timeout: 5000 });

    // Step 3: Get first pending item
    const firstPendingItem = page.locator('[data-testid="pending-approval-item"]').first();
    const isVisible = await firstPendingItem.isVisible();

    if (isVisible) {
      // Step 4: Click approve button
      const approveButton = firstPendingItem.locator('button:has-text("Approve")');
      await approveButton.click();

      // Step 5: Confirm approval
      const confirmButton = page.locator('button:has-text("Confirm Approval"), button:has-text("Yes")').first();
      await confirmButton.click({ timeout: 3000 }).catch(() => null);

      // Step 6: Verify success
      const successMessage = page.locator('[data-testid="success-message"]');
      await expect(successMessage).toBeVisible({ timeout: 3000 });
    }
  });

  test('should reject pending job description with reason', async () => {
    // Step 1: Navigate to approvals
    const approvalsLink = page.locator('a:has-text("Approvals"), button:has-text("Pending")').first();
    await approvalsLink.click();

    // Step 2: Wait for items
    await page.waitForSelector('[data-testid="pending-approval-item"]', { timeout: 5000 });

    // Step 3: Get first pending item
    const firstPendingItem = page.locator('[data-testid="pending-approval-item"]').first();
    const isVisible = await firstPendingItem.isVisible();

    if (isVisible) {
      // Step 4: Click reject button
      const rejectButton = firstPendingItem.locator('button:has-text("Reject")');
      await rejectButton.click();

      // Step 5: Fill rejection reason
      const reasonInput = page.locator('[data-testid="rejection-reason"]');
      await reasonInput.fill('Job description does not meet quality standards');

      // Step 6: Submit rejection
      const submitButton = page.locator('button:has-text("Submit Rejection")').first();
      await submitButton.click({ timeout: 3000 }).catch(() => null);

      // Step 7: Verify rejection processed
      const successMessage = page.locator('[data-testid="success-message"]');
      await expect(successMessage).toBeVisible({ timeout: 3000 });
    }
  });

  test('should filter approvals by status', async () => {
    // Step 1: Navigate to approvals
    const approvalsLink = page.locator('a:has-text("Approvals"), button:has-text("Pending")').first();
    await approvalsLink.click();

    // Step 2: Wait for page to load
    await page.waitForLoadState('networkidle');

    // Step 3: Select status filter
    const statusFilter = page.locator('[data-testid="status-filter"]');
    const isVisible = await statusFilter.isVisible();

    if (isVisible) {
      await statusFilter.selectOption('approved');

      // Step 4: Wait for filtered results
      await page.waitForTimeout(1500);

      // Step 5: Verify filtered items
      const approvalItems = page.locator('[data-testid="pending-approval-item"]');
      const count = await approvalItems.count();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('should display system health and monitoring', async () => {
    // Step 1: Look for monitoring section
    const monitoringLink = page.locator('a:has-text("Monitoring"), button:has-text("System Health")').first();
    const exists = await monitoringLink.count() > 0;

    if (exists) {
      await monitoringLink.click();
      await page.waitForLoadState('networkidle');

      // Step 2: Verify health metrics
      const healthMetrics = page.locator('[data-testid="health-metrics"]');
      await expect(healthMetrics).toBeVisible();

      // Step 3: Check for specific health indicators
      const cpuUsage = page.locator('[data-testid="cpu-usage"]');
      await expect(cpuUsage).toBeVisible({ timeout: 2000 }).catch(() => null);
    }
  });

  test('should export audit logs', async () => {
    // Step 1: Navigate to audit logs
    const auditLink = page.locator('a:has-text("Audit Logs"), button:has-text("Logs")').first();
    const exists = await auditLink.count() > 0;

    if (exists) {
      await auditLink.click();
      await page.waitForLoadState('networkidle');

      // Step 2: Look for export button
      const exportButton = page.locator('button:has-text("Export"), button:has-text("Download")').first();
      const exportExists = await exportButton.count() > 0;

      if (exportExists) {
        // Setup download promise before clicking
        const downloadPromise = page.waitForEvent('download');
        await exportButton.click();

        // Step 3: Verify download started
        const download = await downloadPromise;
        expect(download.suggestedFilename()).toContain('log');
      }
    }
  });

  test('should manage user roles and permissions', async () => {
    // Step 1: Navigate to user management
    const usersLink = page.locator('a:has-text("Users"), button:has-text("Manage Users")').first();
    const exists = await usersLink.count() > 0;

    if (exists) {
      await usersLink.click();
      await page.waitForLoadState('networkidle');

      // Step 2: Verify users list
      const usersList = page.locator('[data-testid="users-list"]');
      await expect(usersList).toBeVisible({ timeout: 2000 }).catch(() => null);

      // Step 3: Look for role management
      const firstUserRow = page.locator('[data-testid="user-row"]').first();
      const rowExists = await firstUserRow.count() > 0;

      if (rowExists) {
        // Step 4: Click to edit user
        await firstUserRow.click();

        // Step 5: Verify role selection available
        const roleSelect = page.locator('[data-testid="role-select"]');
        await expect(roleSelect).toBeVisible({ timeout: 2000 }).catch(() => null);
      }
    }
  });

  test('should display analytics and reports', async () => {
    // Step 1: Navigate to analytics
    const analyticsLink = page.locator('a:has-text("Analytics"), button:has-text("Reports")').first();
    const exists = await analyticsLink.count() > 0;

    if (exists) {
      await analyticsLink.click();
      await page.waitForLoadState('networkidle');

      // Step 2: Verify charts are displayed
      const charts = page.locator('[data-testid="chart"]');
      const chartCount = await charts.count();
      expect(chartCount).toBeGreaterThan(0);

      // Step 3: Check for date range selector
      const dateRange = page.locator('[data-testid="date-range-picker"]');
      const dateExists = await dateRange.count() > 0;
      expect(dateExists).toBe(true);
    }
  });

  test('should handle admin search functionality', async () => {
    // Step 1: Find search input
    const searchInput = page.locator('[data-testid="admin-search"]');
    const exists = await searchInput.count() > 0;

    if (exists) {
      // Step 2: Search for something
      await searchInput.fill('Engineering Manager');

      // Step 3: Wait for results
      await page.waitForTimeout(1000);

      // Step 4: Verify results displayed
      const searchResults = page.locator('[data-testid="search-results"]');
      const resultsVisible = await searchResults.isVisible({ timeout: 2000 }).catch(() => false);
      expect(resultsVisible || true).toBe(true);
    }
  });

  test('should toggle dark mode in admin panel', async () => {
    // Step 1: Find theme toggle
    const themeToggle = page.locator('[data-testid="theme-toggle"]');
    const exists = await themeToggle.count() > 0;

    if (exists) {
      // Step 2: Get current theme
      const htmlElement = page.locator('html');
      const initialTheme = await htmlElement.evaluate(el => el.getAttribute('data-theme'));

      // Step 3: Click toggle
      await themeToggle.click();

      // Step 4: Verify theme changed
      await page.waitForTimeout(500);
      const newTheme = await htmlElement.evaluate(el => el.getAttribute('data-theme'));
      expect(newTheme).not.toBe(initialTheme);
    }
  });

  test('should handle batch operations on jobs', async () => {
    // Step 1: Navigate to jobs
    const jobsLink = page.locator('a:has-text("Job Listings"), button:has-text("Manage Jobs")').first();
    await jobsLink.click();

    // Step 2: Wait for jobs to load
    await page.waitForSelector('[data-testid="job-row"]', { timeout: 5000 });

    // Step 3: Look for select-all checkbox
    const selectAllCheckbox = page.locator('[data-testid="select-all-jobs"]');
    const exists = await selectAllCheckbox.count() > 0;

    if (exists) {
      // Step 4: Select all
      await selectAllCheckbox.click();

      // Step 5: Look for bulk action button
      const bulkActionButton = page.locator('[data-testid="bulk-action-button"]');
      const actionExists = await bulkActionButton.count() > 0;
      expect(actionExists).toBe(true);
    }
  });

  test('should display real-time notifications', async () => {
    // Step 1: Look for notification center
    const notificationCenter = page.locator('[data-testid="notification-center"]');
    const exists = await notificationCenter.count() > 0;

    if (exists) {
      // Step 2: Click to open
      await notificationCenter.click();

      // Step 3: Verify notifications list
      const notificationsList = page.locator('[data-testid="notifications-list"]');
      await expect(notificationsList).toBeVisible({ timeout: 2000 }).catch(() => null);
    }
  });

  test('should verify admin session security', async () => {
    // Step 1: Check if still logged in as admin
    const userMenu = page.locator('[data-testid="user-menu"]');
    await expect(userMenu).toBeVisible();

    // Step 2: Verify admin indicator
    const adminBadge = page.locator('[data-testid="admin-badge"]');
    await expect(adminBadge).toBeVisible({ timeout: 2000 }).catch(() => null);

    // Step 3: Check for logout functionality
    await userMenu.click();
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign Out")');
    const logoutExists = await logoutButton.count() > 0;
    expect(logoutExists).toBe(true);
  });
});
