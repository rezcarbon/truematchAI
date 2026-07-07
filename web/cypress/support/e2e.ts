// Cypress E2E Support File
// This file is loaded before every test file

// Import commands
import './commands';

// Disable uncaught exception handling for specific errors
Cypress.on('uncaught:exception', (err, runnable) => {
  // Return false to prevent Cypress from failing the test
  // when specific errors occur
  if (
    err.message.includes('ResizeObserver') ||
    err.message.includes('Can\'t perform a React state update')
  ) {
    return false;
  }
  return true;
});

// Global test hooks
beforeEach(() => {
  // Clear localStorage
  cy.clearLocalStorage();

  // Clear session storage
  cy.window().then((win) => {
    win.sessionStorage.clear();
  });

  // Set test mode flag
  cy.window().then((win) => {
    (win as any).__CYPRESS_TEST__ = true;
  });
});

afterEach(() => {
  // Log any console errors
  cy.window().then((win) => {
    const logs = (win.console as any).__logs;
    if (logs) {
      logs.forEach((log: any) => {
        if (log.type === 'error') {
          cy.log('Console Error: ' + log.message);
        }
      });
    }
  });
});
