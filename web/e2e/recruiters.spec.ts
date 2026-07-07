import { test, expect, Page } from '@playwright/test';

/**
 * E2E Tests for Recruiter Workflows
 * Tests: Create JD → Simulate → Create position → Review candidates → Make decision
 */

test.describe('Recruiter Workflows', () => {
  let page: Page;

  test.beforeEach(async ({ page: p }) => {
    page = p;
    // Navigate to recruiter dashboard
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should create and simulate job description', async () => {
    // Step 1: Navigate to JD optimizer
    await page.click('text=JD Optimizer');
    await page.waitForLoadState('networkidle');

    // Step 2: Fill job description form
    const jdTextarea = page.locator('textarea[placeholder*="Paste the complete job description"]');
    const fullJD = `We are seeking a Senior Full Stack Engineer with 5+ years of experience.

Responsibilities:
- Design and implement scalable backend systems
- Develop responsive frontend interfaces
- Lead technical architecture decisions
- Mentor junior engineers

Requirements:
- 5+ years of software engineering experience
- Strong knowledge of React and Node.js
- Experience with PostgreSQL and Redis
- Understanding of cloud infrastructure (AWS/GCP)
- Excellent communication and leadership skills

Nice to have:
- Experience with Kubernetes and Docker
- Open source contributions
- Previous startup experience`;

    await jdTextarea.fill(fullJD);

    // Step 3: Fill position title
    const titleInput = page.locator('input[placeholder*="Senior Backend Engineer"]');
    await titleInput.fill('Senior Full Stack Engineer');

    // Step 4: Run simulation
    const runButton = page.locator('button:has-text("Run Simulation")');
    await runButton.click();

    // Step 5: Wait for simulation results
    await page.waitForSelector('[data-testid="simulation-results"]', { timeout: 10000 });

    // Step 6: Verify results display
    const resultsSection = page.locator('[data-testid="simulation-results"]');
    await expect(resultsSection).toBeVisible();

    const requirementsCoverage = page.locator('[data-testid="requirements-coverage"]');
    await expect(requirementsCoverage).toBeVisible();
  });

  test('should review simulation insights and recommendations', async () => {
    // Step 1: Run a simulation first
    await page.click('text=JD Optimizer');
    await page.waitForLoadState('networkidle');

    const jdTextarea = page.locator('textarea[placeholder*="Paste the complete job description"]');
    await jdTextarea.fill('We need a Senior Engineer with 5+ years experience in React and Node.js');

    const titleInput = page.locator('input[placeholder*="Senior Backend Engineer"]');
    await titleInput.fill('Senior Engineer');

    const runButton = page.locator('button:has-text("Run Simulation")');
    await runButton.click();

    await page.waitForSelector('[data-testid="simulation-results"]');

    // Step 2: Review insights
    const insightsSection = page.locator('[data-testid="insights-section"]');
    await expect(insightsSection).toBeVisible();

    // Step 3: Check recommendations
    const recommendations = page.locator('[data-testid="recommendations"]');
    await expect(recommendations).toBeVisible();

    const recommendationItems = recommendations.locator('[data-testid="recommendation-item"]');
    const count = await recommendationItems.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should create position from job description', async () => {
    // Step 1: Navigate to positions
    await page.click('text=Positions');
    await page.waitForLoadState('networkidle');

    // Step 2: Click create position
    const createButton = page.locator('button:has-text("Create Position")');
    await createButton.click();

    // Step 3: Fill position form
    const titleInput = page.locator('input[name="title"]');
    await titleInput.fill('Senior React Developer');

    const locationInput = page.locator('input[name="location"]');
    await locationInput.fill('San Francisco, CA');

    const descriptionTextarea = page.locator('textarea[name="description"]');
    await descriptionTextarea.fill('We are looking for a Senior React Developer with 5+ years experience');

    const salaryInput = page.locator('input[name="salary"]');
    await salaryInput.fill('150000-200000');

    // Step 4: Submit position
    const submitButton = page.locator('button:has-text("Create Position")');
    await submitButton.click();

    // Step 5: Verify position created
    const successMessage = page.locator('[data-testid="success-message"]');
    await expect(successMessage).toBeVisible();
    await expect(successMessage).toContainText('Position created');
  });

  test('should review and rank candidates', async () => {
    // Step 1: Navigate to candidates
    await page.click('text=Candidates');
    await page.waitForLoadState('networkidle');

    // Step 2: Filter by position
    const positionFilter = page.locator('[data-testid="position-filter"]');
    await positionFilter.selectOption('Senior React Developer');

    // Step 3: Wait for candidates to load
    await page.waitForSelector('[data-testid="candidate-card"]');

    // Step 4: Click first candidate
    const firstCandidate = page.locator('[data-testid="candidate-card"]').first();
    await firstCandidate.click();

    // Step 5: Verify candidate details
    const candidateProfile = page.locator('[data-testid="candidate-profile"]');
    await expect(candidateProfile).toBeVisible();

    // Step 6: Check match score and skills
    const matchScore = page.locator('[data-testid="match-score"]');
    await expect(matchScore).toBeVisible();

    const skillsRadar = page.locator('[data-testid="skills-radar"]');
    await expect(skillsRadar).toBeVisible();

    // Step 7: Rate candidate
    const ratingButtons = page.locator('button[data-rating]');
    await ratingButtons.nth(4).click(); // 5-star rating

    // Step 8: Add notes
    const notesTextarea = page.locator('textarea[name="notes"]');
    await notesTextarea.fill('Strong technical background, excellent communication');

    const saveButton = page.locator('button:has-text("Save")');
    await saveButton.click();

    const savedMessage = page.locator('[data-testid="saved-message"]');
    await expect(savedMessage).toBeVisible();
  });

  test('should manage candidate pipeline stages', async () => {
    // Step 1: Navigate to pipeline
    await page.click('text=Pipeline');
    await page.waitForLoadState('networkidle');

    // Step 2: Verify pipeline stages
    const stages = ['Applied', 'Screening', 'Interview', 'Offer', 'Rejected'];
    for (const stage of stages) {
      const stageColumn = page.locator(`[data-testid="stage-${stage.toLowerCase()}"]`);
      await expect(stageColumn).toBeVisible();
    }

    // Step 3: Drag candidate to next stage
    const candidateCard = page.locator('[data-testid="candidate-card"]').first();
    const interviewColumn = page.locator('[data-testid="stage-interview"]');

    await candidateCard.dragTo(interviewColumn);

    // Step 4: Verify candidate moved
    await page.waitForTimeout(500);
    const updatedMessage = page.locator('[data-testid="updated-message"]');
    await expect(updatedMessage).toBeVisible();
  });

  test('should send offer to selected candidate', async () => {
    // Step 1: Navigate to candidates
    await page.click('text=Candidates');
    await page.waitForLoadState('networkidle');

    // Step 2: Find candidate in offer stage
    const candidateCard = page.locator('[data-testid="candidate-card"]').first();
    await candidateCard.click();

    // Step 3: Click make offer
    const offerButton = page.locator('button:has-text("Send Offer")');
    await offerButton.click();

    // Step 4: Fill offer details
    const modal = page.locator('[data-testid="offer-modal"]');
    await expect(modal).toBeVisible();

    const salaryInput = page.locator('input[name="salary"]', { root: modal });
    await salaryInput.fill('175000');

    const startDateInput = page.locator('input[name="startDate"]', { root: modal });
    await startDateInput.fill('2024-03-01');

    // Step 5: Send offer
    const sendButton = page.locator('button:has-text("Send Offer")', { root: modal });
    await sendButton.click();

    // Step 6: Verify offer sent
    const successMessage = page.locator('[data-testid="offer-sent-message"]');
    await expect(successMessage).toBeVisible();
  });

  test('should track candidate communications', async () => {
    // Step 1: Navigate to candidates
    await page.click('text=Candidates');
    await page.waitForLoadState('networkidle');

    // Step 2: Open candidate
    const candidateCard = page.locator('[data-testid="candidate-card"]').first();
    await candidateCard.click();

    // Step 3: View communication history
    const communicationTab = page.locator('button:has-text("Communications")');
    await communicationTab.click();

    // Step 4: Verify history displays
    const communicationHistory = page.locator('[data-testid="communication-history"]');
    await expect(communicationHistory).toBeVisible();

    const messages = page.locator('[data-testid="message"]');
    const count = await messages.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should generate job matching reports', async () => {
    // Step 1: Navigate to reports
    await page.click('text=Reports');
    await page.waitForLoadState('networkidle');

    // Step 2: Select position for report
    const positionSelect = page.locator('[data-testid="position-select"]');
    const options = positionSelect.locator('option');
    const firstOption = options.nth(1);
    await firstOption.click();

    // Step 3: Generate report
    const generateButton = page.locator('button:has-text("Generate Report")');
    await generateButton.click();

    // Step 4: Wait for report
    await page.waitForSelector('[data-testid="report-content"]', { timeout: 10000 });

    // Step 5: Verify report displays
    const reportContent = page.locator('[data-testid="report-content"]');
    await expect(reportContent).toBeVisible();

    // Step 6: Check report sections
    const matchingMetrics = page.locator('[data-testid="matching-metrics"]');
    await expect(matchingMetrics).toBeVisible();
  });

  test('should complete end-to-end recruiter workflow', async () => {
    // Step 1: Simulate JD
    await page.click('text=JD Optimizer');
    await page.waitForLoadState('networkidle');

    const jdTextarea = page.locator('textarea[placeholder*="Paste the complete job description"]');
    await jdTextarea.fill('Senior Engineer with React experience');

    const titleInput = page.locator('input[placeholder*="Senior Backend Engineer"]');
    await titleInput.fill('Senior React Engineer');

    let runButton = page.locator('button:has-text("Run Simulation")');
    await runButton.click();
    await page.waitForSelector('[data-testid="simulation-results"]');

    // Step 2: Create position
    await page.click('text=Positions');
    await page.waitForLoadState('networkidle');

    let createButton = page.locator('button:has-text("Create Position")');
    await createButton.click();

    let titleInput2 = page.locator('input[name="title"]');
    await titleInput2.fill('Senior React Engineer');

    let descTextarea = page.locator('textarea[name="description"]');
    await descTextarea.fill('Senior React Engineer with 5+ years experience');

    let submitButton = page.locator('button:has-text("Create Position")');
    await submitButton.click();

    await page.waitForSelector('[data-testid="success-message"]');

    // Step 3: Review candidates
    await page.click('text=Candidates');
    await page.waitForLoadState('networkidle');

    let candidateCard = page.locator('[data-testid="candidate-card"]').first();
    await candidateCard.click();

    // Step 4: Rate candidate
    let ratingButtons = page.locator('button[data-rating]');
    await ratingButtons.nth(4).click();

    let saveButton = page.locator('button:has-text("Save")');
    await saveButton.click();

    // Step 5: Send offer
    let offerButton = page.locator('button:has-text("Send Offer")');
    if (await offerButton.isVisible()) {
      await offerButton.click();

      let modal = page.locator('[data-testid="offer-modal"]');
      if (await modal.isVisible()) {
        let salaryInput = page.locator('input[name="salary"]', { root: modal });
        await salaryInput.fill('180000');

        let sendButton = page.locator('button:has-text("Send Offer")', { root: modal });
        await sendButton.click();

        await page.waitForSelector('[data-testid="offer-sent-message"]');
      }
    }
  });
});

test.describe('Recruiter Error Handling', () => {
  let page: Page;

  test.beforeEach(async ({ page: p }) => {
    page = p;
    await page.goto('/recruiter/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should handle invalid job description submission', async () => {
    await page.click('text=JD Optimizer');
    await page.waitForLoadState('networkidle');

    const jdTextarea = page.locator('textarea[placeholder*="Paste the complete job description"]');
    await jdTextarea.fill('Short');

    const runButton = page.locator('button:has-text("Run Simulation")');
    // Button should be disabled
    const isDisabled = await runButton.isDisabled();
    expect(isDisabled).toBeTruthy();
  });

  test('should handle duplicate position creation', async () => {
    await page.click('text=Positions');
    await page.waitForLoadState('networkidle');

    const createButton = page.locator('button:has-text("Create Position")');
    await createButton.click();

    const titleInput = page.locator('input[name="title"]');
    await titleInput.fill('Senior Engineer');

    const submitButton = page.locator('button:has-text("Create Position")');
    await submitButton.click();

    await page.waitForSelector('[data-testid="success-message"]');

    // Try to create duplicate
    await createButton.click();
    await titleInput.fill('Senior Engineer');
    await submitButton.click();

    const errorMessage = page.locator('[data-testid="error-message"]');
    await expect(errorMessage).toBeVisible();
  });

  test('should handle missing required fields', async () => {
    await page.click('text=Positions');
    await page.waitForLoadState('networkidle');

    const createButton = page.locator('button:has-text("Create Position")');
    await createButton.click();

    const submitButton = page.locator('button:has-text("Create Position")');
    await submitButton.click();

    const validationError = page.locator('[data-testid="validation-error"]');
    await expect(validationError).toBeVisible();
  });
});
