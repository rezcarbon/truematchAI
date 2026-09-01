# Jest Testing Quick Start Guide

## Installation

```bash
cd web
npm install
```

## Run Tests

### Run all tests
```bash
npm test
```

### Run in watch mode (for development)
```bash
npm run test:watch
```

### Generate coverage report
```bash
npm run test:coverage
```

### Run for CI/CD
```bash
npm run test:ci
```

## View Results

### Console Output
Tests pass/fail with detailed output showing:
- Test file path
- Test case name
- Pass/fail status
- Error messages if failed

### Coverage Report
After running `npm run test:coverage`:
- **Terminal:** Shows coverage summary by percentage
- **HTML Report:** Open `coverage/index.html` in browser for detailed visual report

## Test Files Location

```
web/
├── jest.config.ts                          ← Configuration
├── jest.setup.ts                           ← Environment setup
├── src/
│   ├── app/(auth)/__tests__/auth.test.tsx                    ← Auth tests (18)
│   ├── components/admin/operators/__tests__/
│   │   ├── QueueTable.test.tsx                              ← Queue table (13)
│   │   └── ActionPanel.test.tsx                             ← Actions (15)
│   ├── hooks/__tests__/useAgentOperator.test.ts             ← WebSocket hook (14)
│   └── lib/__tests__/
│       ├── api.test.ts                                      ← API client (20)
│       ├── utils.test.ts                                    ← Utils (25+)
│       └── test-utils.tsx                                   ← Test helpers
└── __tests__/integration/operator-dashboard.test.tsx        ← Integration (15)
```

## Key Statistics

- **Total Test Files:** 9
- **Total Test Cases:** 120+
- **Total Lines of Test Code:** 3,000+
- **Coverage Target:** 50%+ (branches, functions, lines, statements)
- **Time to Run:** ~10-15 seconds

## Test Coverage by Feature

| Feature | Tests | File |
|---------|-------|------|
| Authentication | 18 | `auth.test.tsx` |
| Queue Table | 13 | `QueueTable.test.tsx` |
| Action Panel | 15 | `ActionPanel.test.tsx` |
| WebSocket Hook | 14 | `useAgentOperator.test.ts` |
| API Client | 20 | `api.test.ts` |
| Utilities | 25+ | `utils.test.ts` |
| Integration | 15 | `operator-dashboard.test.tsx` |

## Common Commands

### Run specific test file
```bash
npm test -- auth.test.tsx
```

### Run specific test case
```bash
npm test -- auth.test.tsx -t "renders login form"
```

### Update snapshots
```bash
npm test -- -u
```

### Run tests matching pattern
```bash
npm test -- --testNamePattern="Queue"
```

### Clear cache and run
```bash
npm test -- --clearCache
```

## Debugging

### Run tests with debugging enabled
```bash
node --inspect-brk node_modules/.bin/jest --runInBand
```

### View only failing tests
```bash
npm test -- --onlyChanged
```

### Verbose output
```bash
npm test -- --verbose
```

## Documentation

- **TESTING.md** - Comprehensive testing guide with best practices
- **TEST_SUMMARY.md** - Detailed summary of all tests and coverage

## CI/CD

Tests automatically run on:
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Changes to `web/` directory

See `.github/workflows/test.yml` for workflow details.

## Troubleshooting

### Tests won't run
```bash
# Clear cache and reinstall
rm -rf node_modules/.cache
npm install
npm test
```

### Module not found error
```bash
# Check jest.config.ts moduleNameMapper
# Ensure @/ paths are configured correctly
```

### Timeout errors
```bash
# Increase timeout in jest.config.ts
# testTimeout: 10000,
```

### Mock not working
```bash
# Clear mocks in beforeEach
jest.clearAllMocks()
```

## Next Steps

1. Read [TESTING.md](./TESTING.md) for best practices
2. Write tests for new components using the patterns
3. Aim for 70%+ coverage as development continues
4. Set up pre-commit hooks to run tests automatically

## Support

For issues or questions:
1. Check TESTING.md for detailed documentation
2. Review existing test files for examples
3. See jest.setup.ts for mock configurations
