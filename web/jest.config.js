// CommonJS config so Jest can load it without `ts-node` (which is not a direct
// dependency and is not reliably installed under `npm ci`). Behaviour is
// identical to the previous jest.config.ts.
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

/** @type {import('jest').Config} */
const config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  // Match only *.test / *.spec files so non-test helpers living under __tests__
  // (e.g. test-utils.tsx) are not collected as empty suites.
  testMatch: ['**/?(*.)+(spec|test).ts?(x)'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.tsx',
    '!src/**/__tests__/**',
    '!src/app/api/**',
    '!src/middleware.ts',
  ],
  // Progressive coverage thresholds targeting 80%+ for all components
  // Phase 1 (Current): Enforce minimum baseline
  // Phase 2 (Month 1): Increase to 45/35/40/40
  // Phase 3 (Month 2): Increase to 60/55/60/60
  // Phase 4 (Final): Reach 75+/80+/80+/80+
  coverageThreshold: {
    global: {
      branches: 30,
      functions: 15,
      lines: 5,
      statements: 5,
    },
    './src/components/': {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50,
    },
    './src/hooks/': {
      branches: 60,
      functions: 60,
      lines: 60,
      statements: 60,
    },
    './src/lib/': {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  testPathIgnorePatterns: ['/node_modules/', '/.next/'],
  transformIgnorePatterns: ['/node_modules/', '^.+\\.module\\.(css|sass|scss)$'],
  moduleDirectories: ['node_modules', '<rootDir>/'],
}

module.exports = createJestConfig(config)
