/**
 * CYPRESS E2E TESTS: Complex Interactions
 *
 * These tests focus on complex user interactions that benefit from
 * Cypress's ability to handle real browser state and animations.
 */

describe('Table Interactions', () => {
  beforeEach(() => {
    cy.visit('/recruiter/candidates');
    cy.wait(500);
  });

  it('should sort table by clicking column headers', () => {
    // Get initial order
    cy.get('[data-testid="candidate-table"] tbody tr').then((rows) => {
      const firstNameBefore = rows.eq(0).find('td').eq(0).text();

      // Click sort by name
      cy.get('[data-testid="candidate-table"] th')
        .contains('Name')
        .click();

      cy.wait(300);

      // Verify order has changed
      cy.get('[data-testid="candidate-table"] tbody tr').then((newRows) => {
        const firstNameAfter = newRows.eq(0).find('td').eq(0).text();
        expect(firstNameAfter).not.to.equal(firstNameBefore);
      });
    });
  });

  it('should filter table by multiple criteria', () => {
    // Open filters
    cy.get('[data-testid="filters-button"]').click();

    // Add skill filter
    cy.get('[data-testid="filter-skills"]').within(() => {
      cy.get('input').type('React');
      cy.contains('React').click();
    });

    // Add experience filter
    cy.get('[data-testid="filter-experience"]').within(() => {
      cy.get('input').type('5+');
      cy.contains('5+ years').click();
    });

    // Apply filters
    cy.get('[data-testid="apply-filters-button"]').click();

    // Verify table is filtered
    cy.get('[data-testid="candidate-table"] tbody tr').each((row) => {
      cy.wrap(row).should('contain', 'React');
    });
  });

  it('should paginate through table', () => {
    // Verify rows are displayed
    cy.get('[data-testid="candidate-table"] tbody tr').should('have.length.greaterThan', 0);

    // Click next page
    cy.get('[data-testid="pagination"] [aria-label="Next page"]').click();

    cy.wait(300);

    // Verify new rows are displayed
    cy.get('[data-testid="candidate-table"] tbody tr')
      .first()
      .should('be.visible');

    // Click previous page
    cy.get('[data-testid="pagination"] [aria-label="Previous page"]').click();

    cy.wait(300);

    // Should be back on first page
    cy.get('[data-testid="candidate-table"] tbody tr')
      .first()
      .should('be.visible');
  });

  it('should select multiple rows with checkbox', () => {
    // Click header checkbox to select all
    cy.get('[data-testid="select-all-checkbox"]').click();

    cy.wait(200);

    // Verify all rows are selected
    cy.get('[data-testid="candidate-table"] tbody input[type="checkbox"]').each(
      (checkbox) => {
        cy.wrap(checkbox).should('be.checked');
      }
    );

    // Verify action buttons appear
    cy.get('[data-testid="batch-actions"]').should('be.visible');

    // Click to deselect all
    cy.get('[data-testid="select-all-checkbox"]').click();

    cy.wait(200);

    // Verify none are selected
    cy.get('[data-testid="candidate-table"] tbody input[type="checkbox"]').each(
      (checkbox) => {
        cy.wrap(checkbox).should('not.be.checked');
      }
    );
  });

  it('should expand row details', () => {
    // Click expand button on first row
    cy.get('[data-testid="candidate-table"] tbody tr')
      .first()
      .find('[data-testid="expand-button"]')
      .click();

    cy.wait(300);

    // Verify details panel appears
    cy.get('[data-testid="candidate-details"]').should('be.visible');

    // Verify detailed information is shown
    cy.get('[data-testid="candidate-details"]')
      .within(() => {
        cy.get('[data-testid="skills-section"]').should('be.visible');
        cy.get('[data-testid="experience-section"]').should('be.visible');
      });

    // Click collapse
    cy.get('[data-testid="candidate-table"] tbody tr')
      .first()
      .find('[data-testid="collapse-button"]')
      .click();

    cy.wait(300);

    cy.get('[data-testid="candidate-details"]').should('not.be.visible');
  });

  it('should search within table', () => {
    // Enter search term
    cy.get('[data-testid="table-search"]').type('John Doe');

    cy.wait(500);

    // Verify results are filtered
    cy.get('[data-testid="candidate-table"] tbody tr').each((row) => {
      cy.wrap(row).should('contain', 'John Doe');
    });

    // Clear search
    cy.get('[data-testid="table-search"]').clear();

    cy.wait(500);

    // Verify all results are shown again
    cy.get('[data-testid="candidate-table"] tbody tr').should(
      'have.length.greaterThan',
      1
    );
  });
});

describe('Form Interactions', () => {
  beforeEach(() => {
    cy.visit('/recruiter/jd-optimizer');
  });

  it('should validate form fields on blur', () => {
    // Get JD textarea
    cy.get('[data-testid="jd-textarea"]').click().blur();

    // Verify error message appears
    cy.get('[data-testid="jd-error"]').should(
      'contain',
      'Job description is required'
    );

    // Enter valid text
    cy.get('[data-testid="jd-textarea"]').type('Senior Developer needed');

    // Error should disappear
    cy.get('[data-testid="jd-error"]').should('not.exist');
  });

  it('should show/hide optional fields conditionally', () => {
    // Enable advanced options
    cy.get('[data-testid="show-advanced-options"]').click();

    cy.wait(200);

    // Verify additional fields appear
    cy.get('[data-testid="salary-field"]').should('be.visible');
    cy.get('[data-testid="location-field"]').should('be.visible');

    // Disable advanced options
    cy.get('[data-testid="hide-advanced-options"]').click();

    cy.wait(200);

    // Fields should be hidden
    cy.get('[data-testid="salary-field"]').should('not.be.visible');
  });

  it('should autosave form progress', () => {
    // Type into textarea
    cy.get('[data-testid="jd-textarea"]').type('Senior Software Engineer');

    // Wait for autosave
    cy.wait(1000);

    // Verify autosave indicator appears
    cy.get('[data-testid="autosave-indicator"]').should(
      'contain',
      'Saved'
    );

    // Refresh page
    cy.reload();

    cy.wait(500);

    // Verify content is still there
    cy.get('[data-testid="jd-textarea"]').should(
      'have.value',
      'Senior Software Engineer'
    );
  });

  it('should handle form submission with loading state', () => {
    // Fill form
    cy.get('[data-testid="jd-textarea"]').type('DevOps Engineer');

    // Submit
    cy.get('[data-testid="submit-button"]').click();

    // Verify loading state
    cy.get('[data-testid="submit-button"]').should('have.attr', 'disabled');
    cy.get('[data-testid="loading-spinner"]').should('be.visible');

    // Wait for completion
    cy.get('[data-testid="success-message"]', { timeout: 5000 }).should(
      'be.visible'
    );

    // Button should be enabled again
    cy.get('[data-testid="submit-button"]').should('not.have.attr', 'disabled');
  });
});

describe('Modal Interactions', () => {
  beforeEach(() => {
    cy.visit('/candidate/dashboard');
  });

  it('should open and close modal', () => {
    // Modal should not be visible initially
    cy.get('[data-testid="resume-upload-modal"]').should('not.be.visible');

    // Click to open
    cy.get('[data-testid="upload-resume-button"]').click();

    // Modal should be visible
    cy.get('[data-testid="resume-upload-modal"]').should('be.visible');

    // Close with button
    cy.get('[data-testid="modal-close-button"]').click();

    // Modal should be hidden
    cy.get('[data-testid="resume-upload-modal"]').should('not.be.visible');

    // Open again
    cy.get('[data-testid="upload-resume-button"]').click();

    // Close with escape key
    cy.get('body').type('{esc}');

    // Modal should be hidden
    cy.get('[data-testid="resume-upload-modal"]').should('not.be.visible');
  });

  it('should handle stacked modals', () => {
    // Open first modal
    cy.get('[data-testid="upload-resume-button"]').click();
    cy.get('[data-testid="resume-upload-modal"]').should('be.visible');

    // Open nested modal (e.g., help)
    cy.get('[data-testid="help-button"]').click();
    cy.get('[data-testid="help-modal"]').should('be.visible');

    // Close nested modal
    cy.get('[data-testid="help-modal"] [data-testid="modal-close-button"]').click();

    cy.wait(200);

    // First modal should still be visible
    cy.get('[data-testid="resume-upload-modal"]').should('be.visible');
    cy.get('[data-testid="help-modal"]').should('not.be.visible');

    // Close first modal
    cy.get('[data-testid="resume-upload-modal"] [data-testid="modal-close-button"]').click();

    cy.wait(200);

    cy.get('[data-testid="resume-upload-modal"]').should('not.be.visible');
  });

  it('should preserve modal state during interaction', () => {
    // Open modal
    cy.get('[data-testid="upload-resume-button"]').click();

    // Fill form
    cy.get('[data-testid="jd-textarea"]').type('Some text');

    // Interact with other elements
    cy.get('[data-testid="modal-footer"] button').click();

    // Modal and text should still be present
    cy.get('[data-testid="resume-upload-modal"]').should('be.visible');
    cy.get('[data-testid="jd-textarea"]').should('have.value', 'Some text');
  });
});

describe('WebSocket Real-time Updates', () => {
  beforeEach(() => {
    cy.visit('/recruiter/applications');
  });

  it('should update applications list in real-time', () => {
    // Get initial count
    cy.get('[data-testid="application-card"]').then((cards) => {
      const initialCount = cards.length;

      // Simulate WebSocket message (in real scenario, use websocket interceptor)
      cy.window().then((win) => {
        // Trigger a simulated update
        if (win.mockWebSocket) {
          win.mockWebSocket.simulateNewApplication();
        }
      });

      cy.wait(500);

      // Verify new application appears
      cy.get('[data-testid="application-card"]').should(
        'have.length',
        initialCount + 1
      );
    });
  });

  it('should update candidate status in real-time', () => {
    // Find a candidate with initial status
    cy.get('[data-testid="candidate-status"]')
      .first()
      .should('contain', 'Applied');

    // Simulate status update
    cy.window().then((win) => {
      if (win.mockWebSocket) {
        win.mockWebSocket.simulateStatusUpdate('accepted');
      }
    });

    cy.wait(500);

    // Status should be updated
    cy.get('[data-testid="candidate-status"]')
      .first()
      .should('contain', 'Accepted');
  });
});

describe('Chart Interactions', () => {
  beforeEach(() => {
    cy.visit('/recruiter/analytics');
  });

  it('should handle chart hover interactions', () => {
    // Hover over chart bar
    cy.get('[data-testid="match-score-chart"] .recharts-bar')
      .first()
      .trigger('mouseover');

    cy.wait(200);

    // Tooltip should appear
    cy.get('[data-testid="chart-tooltip"]').should('be.visible');

    // Move away
    cy.get('body').trigger('mouseout');

    cy.wait(200);

    // Tooltip should disappear
    cy.get('[data-testid="chart-tooltip"]').should('not.be.visible');
  });

  it('should filter chart data', () => {
    // Click filter option
    cy.get('[data-testid="chart-filter"]').click();

    // Select filter
    cy.contains('Last 7 days').click();

    cy.wait(500);

    // Chart should update
    cy.get('[data-testid="match-score-chart"]').should('be.visible');
  });
});

describe('Tab Navigation', () => {
  beforeEach(() => {
    cy.visit('/candidate/dashboard');
  });

  it('should switch tabs and preserve state', () => {
    // Click Resume tab
    cy.get('[data-testid="tab-resumes"]').click();

    // Fill in form/perform actions
    cy.get('[data-testid="search-input"]').type('test');

    cy.wait(300);

    // Switch to Jobs tab
    cy.get('[data-testid="tab-jobs"]').click();

    cy.wait(300);

    // Switch back to Resume tab
    cy.get('[data-testid="tab-resumes"]').click();

    cy.wait(300);

    // Search state should be preserved
    cy.get('[data-testid="search-input"]').should('have.value', 'test');
  });

  it('should update active tab indicator', () => {
    // First tab should be active
    cy.get('[data-testid="tab-resumes"]').parent().should('have.class', 'active');

    // Click another tab
    cy.get('[data-testid="tab-jobs"]').click();

    // Previous tab should not be active
    cy.get('[data-testid="tab-resumes"]').parent().should('not.have.class', 'active');

    // New tab should be active
    cy.get('[data-testid="tab-jobs"]').parent().should('have.class', 'active');
  });
});

describe('Responsive Layout', () => {
  it('should adapt layout for mobile', () => {
    cy.viewport('iphone-12');
    cy.visit('/candidate/dashboard');

    // Sidebar should not be visible on mobile
    cy.get('[data-testid="sidebar"]').should('not.be.visible');

    // Hamburger menu should be visible
    cy.get('[data-testid="mobile-menu"]').should('be.visible');

    // Click to open menu
    cy.get('[data-testid="mobile-menu"]').click();

    // Menu should appear
    cy.get('[data-testid="sidebar"]').should('be.visible');
  });

  it('should adapt layout for tablet', () => {
    cy.viewport('ipad-2');
    cy.visit('/candidate/dashboard');

    // Should show condensed sidebar
    cy.get('[data-testid="sidebar"]').should('be.visible');
    cy.get('[data-testid="sidebar"]').should('have.class', 'condensed');
  });

  it('should adapt layout for desktop', () => {
    cy.viewport(1280, 720);
    cy.visit('/candidate/dashboard');

    // Full sidebar should be visible
    cy.get('[data-testid="sidebar"]').should('be.visible');
    cy.get('[data-testid="sidebar"]').should('not.have.class', 'condensed');
  });
});
