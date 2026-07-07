// Custom Cypress Commands

/**
 * Login command - simulate user login
 */
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.visit('/auth/login');

  // Fill email
  cy.get('[data-testid="email-input"]').type(email);

  // Fill password
  cy.get('[data-testid="password-input"]').type(password);

  // Submit form
  cy.get('[data-testid="login-button"]').click();

  // Wait for redirect
  cy.url().should('not.include', '/auth/login');
});

/**
 * Upload file command
 */
Cypress.Commands.add(
  'uploadFile',
  (
    selector: string,
    fileName: string,
    fileType: string = 'application/pdf'
  ) => {
    cy.get(selector).selectFile(`cypress/fixtures/${fileName}`, {
      force: true,
    });
  }
);

/**
 * Wait for API call
 */
Cypress.Commands.add('waitForAPI', (method: string, url: string) => {
  cy.intercept(method, url).as('apiCall');
  cy.wait('@apiCall');
});

/**
 * Intercept API and mock response
 */
Cypress.Commands.add(
  'mockAPI',
  (method: string, url: string, response: any, statusCode: number = 200) => {
    cy.intercept(method, url, {
      statusCode,
      body: response,
    }).as('mockedCall');
  }
);

/**
 * Check accessibility
 */
Cypress.Commands.add('checkA11y', () => {
  // Basic accessibility checks
  cy.get('button').each((btn) => {
    cy.wrap(btn).should('have.accessible.name');
  });

  cy.get('a').each((link) => {
    // Links should either have text content or aria-label
    const hasText = Cypress.$(link).text().trim().length > 0;
    const hasLabel = Cypress.$(link).attr('aria-label');
    expect(hasText || hasLabel).to.be.true;
  });

  cy.get('input, textarea, select').each((input) => {
    // Form inputs should be associated with labels
    const inputId = Cypress.$(input).attr('id');
    if (inputId) {
      cy.get(`label[for="${inputId}"]`).should('exist');
    }
  });
});

/**
 * Wait for table to load
 */
Cypress.Commands.add('waitForTable', () => {
  cy.get('[role="table"]').should('be.visible');
  cy.get('[role="table"] tbody tr').should('have.length.greaterThan', 0);
});

/**
 * Filter table by column
 */
Cypress.Commands.add(
  'filterTableColumn',
  (columnName: string, filterValue: string) => {
    // Find filter button for column
    cy.get('[role="table"] th').contains(columnName).parent().find('[data-testid="filter-button"]').click();

    // Enter filter value
    cy.get('[data-testid="filter-input"]').type(filterValue);

    // Apply filter
    cy.get('[data-testid="apply-filter-button"]').click();
  }
);

/**
 * Select table row
 */
Cypress.Commands.add('selectTableRow', (rowIndex: number) => {
  cy.get(`[role="table"] tbody tr:eq(${rowIndex}) input[type="checkbox"]`).click();
});

/**
 * Wait for modal
 */
Cypress.Commands.add('waitForModal', () => {
  cy.get('[role="dialog"]').should('be.visible');
});

/**
 * Close modal
 */
Cypress.Commands.add('closeModal', () => {
  cy.get('[role="dialog"] button[aria-label="Close"]').click();
  cy.get('[role="dialog"]').should('not.exist');
});

/**
 * Fill form field
 */
Cypress.Commands.add(
  'fillFormField',
  (label: string, value: string) => {
    cy.contains('label', label)
      .parent()
      .find('input, textarea, select')
      .type(value);
  }
);

/**
 * Submit form
 */
Cypress.Commands.add('submitForm', () => {
  cy.get('[data-testid="form"]').within(() => {
    cy.get('button[type="submit"]').click();
  });
});

/**
 * Check toast notification
 */
Cypress.Commands.add('checkToast', (message: string) => {
  cy.get('[role="status"]').should('contain', message);
});

/**
 * Wait for loader to disappear
 */
Cypress.Commands.add('waitForLoading', () => {
  cy.get('[data-testid="loader"], [role="progressbar"]').should('not.exist');
});

/**
 * Capture screenshot with consistent naming
 */
Cypress.Commands.add('captureScreenshot', (name: string) => {
  cy.screenshot(`${Cypress.spec.name}/${name}`, {
    overwrite: true,
  });
});

/**
 * Check element visibility with retry
 */
Cypress.Commands.add('shouldBeVisibleWithRetry', (selector: string) => {
  cy.get(selector, { timeout: 10000 }).should('be.visible');
});

// TypeScript declarations for custom commands
declare global {
  namespace Cypress {
    interface Chainable {
      login(email: string, password: string): Chainable<void>;
      uploadFile(
        selector: string,
        fileName: string,
        fileType?: string
      ): Chainable<void>;
      waitForAPI(method: string, url: string): Chainable<void>;
      mockAPI(
        method: string,
        url: string,
        response: any,
        statusCode?: number
      ): Chainable<void>;
      checkA11y(): Chainable<void>;
      waitForTable(): Chainable<void>;
      filterTableColumn(columnName: string, filterValue: string): Chainable<void>;
      selectTableRow(rowIndex: number): Chainable<void>;
      waitForModal(): Chainable<void>;
      closeModal(): Chainable<void>;
      fillFormField(label: string, value: string): Chainable<void>;
      submitForm(): Chainable<void>;
      checkToast(message: string): Chainable<void>;
      waitForLoading(): Chainable<void>;
      captureScreenshot(name: string): Chainable<void>;
      shouldBeVisibleWithRetry(selector: string): Chainable<void>;
    }
  }
}
