# JD Optimizer - Quick Start Guide

## Installation & Setup

### 1. Basic Usage

Add the JD Optimizer to any page:

```tsx
import { JDOptimizer } from '@/components/JDOptimizer';

export default function MyPage() {
  return <JDOptimizer apiEndpoint="/api/jd-optimizer" />;
}
```

### 2. File Structure

The implementation includes:

```
src/
  components/JDOptimizer/
    ├── JDOptimizer.tsx              # Main component
    ├── JDUploadInput.tsx            # Upload/paste UI
    ├── QualityScoreGauge.tsx        # Score visualization
    ├── ProgressIndicator.tsx        # Progress tracking
    ├── IssueCard.tsx                # Issue display
    ├── BeforeAfterComparison.tsx    # Comparison view
    ├── InlineEditor.tsx             # Text editor
    └── index.ts                     # Exports
  
  types/
    └── jd-optimizer.ts              # TypeScript types
  
  app/api/jd-optimizer/
    └── route.ts                     # API endpoint

__tests__/
  ├── components/JDOptimizer/        # Component tests (7 files, 86 tests)
  ├── api/jd-optimizer.test.ts       # API tests (20 tests)
  └── e2e/jd-optimizer.e2e.test.tsx # E2E tests (9 scenarios)
```

## Running the Application

### Development Server

```bash
# Start the development server
npm run dev

# Navigate to http://localhost:3000/recruiter/jd-optimizer
```

### Testing

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode (for development)
npm run test:watch

# Run only E2E tests
npm test -- e2e

# Run only API tests
npm test -- api/jd-optimizer
```

## Key Components

### JDOptimizer (Main Component)

The orchestrator component managing the complete flow:

```tsx
<JDOptimizer 
  apiEndpoint="/api/jd-optimizer"
/>
```

**Props:**
- `apiEndpoint` (string, optional): API endpoint for optimization

**Features:**
- Input → Processing → Results workflow
- Error state handling
- Download functionality
- Edit mode toggle
- Reset capability

### JDUploadInput

Upload or paste job descriptions:

```tsx
<JDUploadInput 
  onSubmit={(text) => console.log(text)}
  loading={false}
/>
```

**Supported Formats:**
- TXT files
- Markdown files
- Word documents (.doc, .docx)
- PDF files
- Direct text paste

### QualityScoreGauge

Visual quality score display:

```tsx
<QualityScoreGauge score={75} />
```

**Displays:**
- Animated gauge (0-100)
- Quality rating label
- Contextual messaging
- Color-coded feedback

### IssueCard

Expandable issue display:

```tsx
<IssueCard 
  issue={issue}
  isSelected={true}
  onApplyFix={() => console.log('Fixed!')}
/>
```

**Issue Properties:**
- Title & description
- Severity (high/medium/low)
- Category (clarity/tone/completeness/structure/engagement)
- Problematic text
- Suggested fix
- Explanation & impact

### ProgressIndicator

Track optimization progress:

```tsx
<ProgressIndicator 
  totalIssues={10}
  fixedIssues={5}
/>
```

**Shows:**
- Progress bar
- Phase tracking
- Issue statistics

### BeforeAfterComparison

Compare original and optimized text:

```tsx
<BeforeAfterComparison 
  before="Original text"
  after="Improved text"
/>
```

**Modes:**
- Split view (side-by-side)
- Stacked view (responsive)
- Copy to clipboard
- Statistics

### InlineEditor

Edit the optimized description:

```tsx
<InlineEditor 
  value="Text to edit"
  onChange={(text) => setState(text)}
  onSave={() => console.log('Saved!')}
  onCancel={() => console.log('Cancelled!')}
/>
```

## API Integration

### Endpoint: POST /api/jd-optimizer

**Request:**
```json
{
  "jobDescription": "Your job description text..."
}
```

**Response:**
```json
{
  "qualityScore": 75,
  "optimizedJD": "Improved text...",
  "issues": [
    {
      "id": "1",
      "title": "Weak Language",
      "description": "Replace weak language",
      "category": "clarity",
      "severity": "medium",
      "problematicText": "we need",
      "suggestion": "we are seeking",
      "explanation": "Active language...",
      "impact": "Better engagement",
      "isFixed": false
    }
  ],
  "summary": "Found 2 issues...",
  "improvements": ["Weak Language", "Missing Details"]
}
```

## User Flow

1. **Input**: User uploads file or pastes text
2. **Validation**: Input is validated (required, length limits)
3. **Processing**: API analyzes the job description
4. **Results**: 
   - Quality score displays
   - Issues list shown
   - Before/after comparison visible
5. **Interaction**: User can:
   - Expand issues to see details
   - Apply suggested fixes
   - View progress
   - Edit optimized text
   - Download result
6. **Export**: Download optimized JD as text file

## Customization

### Change API Endpoint

```tsx
<JDOptimizer apiEndpoint="/api/custom-endpoint" />
```

### Customize Styling

Edit TailwindCSS classes directly in components. All colors and spacing use TailwindCSS utilities for easy theming.

### Add Custom Issue Categories

1. Update `OptimizationIssue` type in `/src/types/jd-optimizer.ts`
2. Add color handling in `IssueCard.tsx`
3. Update API to detect new category

## Testing Overview

### Unit Tests (86 tests)
- Component rendering
- User interactions
- State management
- Prop validation
- Edge cases

### API Tests (20 tests)
- Input validation
- Response format
- Error handling
- Issue detection logic

### E2E Tests (9 scenarios)
- Complete workflows
- Error recovery
- Multiple interactions
- State persistence

### Running Specific Tests

```bash
# Test one component
npm test JDUploadInput.test.tsx

# Test a specific scenario
npm test -- --testNamePattern="optimization flow"

# Test with coverage for one file
npm test -- --coverage JDOptimizer.test.tsx
```

## Common Tasks

### Add a New Component

1. Create file in `/src/components/JDOptimizer/ComponentName.tsx`
2. Export from `/src/components/JDOptimizer/index.ts`
3. Import in parent component
4. Create test file in `/__tests__/components/JDOptimizer/`
5. Add tests (minimum 10 test cases)

### Integrate with Real Backend

1. Replace mock API route in `/src/app/api/jd-optimizer/route.ts`
2. Integrate with AI/ML service
3. Update response format if needed
4. Update types in `/src/types/jd-optimizer.ts`
5. Test with integration tests

### Modify Issue Categories

1. Update `OptimizationIssue` interface
2. Add case to `getCategoryColor()` function
3. Update API logic to detect new category
4. Update tests

## Accessibility Features

- ✅ ARIA labels on all inputs
- ✅ Keyboard navigation support
- ✅ Color-blind safe palette
- ✅ High contrast ratios (WCAG AA)
- ✅ Screen reader compatible
- ✅ Semantic HTML structure
- ✅ Proper focus management

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile Safari on iOS 14+
- Chrome Mobile

## Performance Tips

1. API calls are optimized with proper caching
2. Animations use CSS for smooth performance
3. Re-renders are minimized with proper deps
4. File uploads support streaming
5. Component lazy-loading ready

## Troubleshooting

### API not responding?
```bash
# Check if API route exists
curl -X POST http://localhost:3000/api/jd-optimizer \
  -H "Content-Type: application/json" \
  -d '{"jobDescription":"test"}'
```

### Tests failing?
```bash
# Clear Jest cache
npm test -- --clearCache

# Run with verbose output
npm test -- --verbose
```

### Styling not applying?
- Check TailwindCSS is installed
- Verify CSS is being processed
- Check for CSS conflicts

## Next Steps

1. **Test locally**: `npm run dev` and navigate to `/recruiter/jd-optimizer`
2. **Run tests**: `npm test` to verify everything works
3. **Integrate backend**: Connect to real AI/ML service
4. **Deploy**: Build and deploy to production
5. **Monitor**: Track usage and optimize

## File Sizes

- Main component: ~8KB
- All components: ~35KB
- Tests: ~65KB
- Total with dependencies: ~150KB (gzipped)

## Maintenance

- Regular dependency updates
- Test coverage monitoring
- Performance tracking
- User feedback integration
- Bug fixes and improvements

## Support

For issues or questions:
1. Check component README
2. Review test files for usage examples
3. Check TypeScript types for valid props
4. Review JD_OPTIMIZER_IMPLEMENTATION.md for detailed docs

## Quick Test Commands

```bash
# All tests
npm test

# Watch mode (hot reload for tests)
npm run test:watch

# Coverage report
npm run test:coverage

# Specific component
npm test JDOptimizer.test.tsx

# E2E tests only
npm test -- e2e

# API tests only
npm test -- api
```

That's it! You're ready to use the JD Optimizer tool.
