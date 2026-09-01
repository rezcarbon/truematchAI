// Component Test Support
// This file is loaded before each component test

import './commands';

// Mount helper for React components
import { mount } from 'cypress/react18';

declare global {
  namespace Cypress {
    interface Chainable {
      mount: typeof mount;
    }
  }
}

Cypress.Commands.add('mount', mount);

// Reset component state between tests
beforeEach(() => {
  cy.viewport(1280, 720);
});

export {};
