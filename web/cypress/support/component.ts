// Component Test Support
// This file is loaded before each component test

import './commands';

// Mount helper for React components
import { mount } from 'cypress/react18';

Cypress.Commands.add('mount', mount);

// Reset component state between tests
beforeEach(() => {
  cy.viewport(1280, 720);
});

export {};
