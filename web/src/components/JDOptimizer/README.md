# JD Optimizer Component

A comprehensive AI-powered Job Description Optimization Tool that helps recruiters improve job descriptions with automated analysis, issue detection, and real-time editing capabilities.

## Features

- **Upload/Paste UI**: Support for both file uploads and text paste
- **AI-Powered Analysis**: Analyzes job descriptions for improvements
- **Quality Score Gauge**: Visual 0-100 score with animated gauge
- **Issue Detection**: Identifies issues with categories and severity levels
- **Per-Issue Cards**: Expandable cards showing problems, suggestions, and explanations
- **Before/After Comparison**: Side-by-side or stacked view comparison
- **Inline Editor**: Edit and refine the optimized job description
- **Progress Indicator**: Track optimization progress with visual indicators
- **Loading/Error States**: Comprehensive state management with user feedback
- **Animations**: Smooth transitions and progress animations
- **Download**: Export optimized JD as text file

## Component Structure

```
JDOptimizer/
├── JDOptimizer.tsx              # Main component orchestrating the flow
├── JDUploadInput.tsx            # Upload/paste input interface
├── QualityScoreGauge.tsx        # Animated quality score visualization
├── ProgressIndicator.tsx        # Progress tracking with phase indicators
├── IssueCard.tsx                # Individual issue card with details
├── BeforeAfterComparison.tsx    # Before/after text comparison
├── InlineEditor.tsx             # Editable text editor
└── index.ts                     # Public exports
```

## Usage

```tsx
import { JDOptimizer } from '@/components/JDOptimizer';

export default function Page() {
  return (
    <JDOptimizer 
      apiEndpoint="/api/jd-optimizer"
    />
  );
}
```

## Props

### JDOptimizer

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `apiEndpoint` | string | '/api/jd-optimizer' | Backend API endpoint for optimization |

## API Integration

The component communicates with the backend API via POST requests:

### Request Format

```json
{
  "jobDescription": "string"
}
```

### Response Format

```json
{
  "qualityScore": number,
  "optimizedJD": string,
  "issues": [
    {
      "id": string,
      "title": string,
      "description": string,
      "category": "clarity" | "tone" | "completeness" | "structure" | "engagement",
      "severity": "high" | "medium" | "low",
      "problematicText": string,
      "suggestion": string,
      "explanation": string,
      "impact": string,
      "isFixed": boolean
    }
  ],
  "summary": string,
  "improvements": string[]
}
```

## Types

All TypeScript types are defined in `/src/types/jd-optimizer.ts`:

- `JDOptimizationResult` - API response format
- `JDOptimizationRequest` - API request format
- `OptimizationIssue` - Individual issue structure
- `JDOptimizationError` - Error response format

## Styling

The component uses:
- **TailwindCSS** for styling
- **Lucide React** for icons
- **clsx** for conditional classes

Supports both light and dark color schemes via CSS variables.

## Testing

### Unit Tests (16+ tests)

Test files cover all components:

- `JDOptimizer.test.tsx` - Main component flow (8 tests)
- `JDUploadInput.test.tsx` - Upload and paste functionality (11 tests)
- `QualityScoreGauge.test.tsx` - Score animation and display (12 tests)
- `IssueCard.test.tsx` - Issue display and interaction (14 tests)
- `ProgressIndicator.test.tsx` - Progress tracking (12 tests)
- `InlineEditor.test.tsx` - Editor functionality (13 tests)
- `BeforeAfterComparison.test.tsx` - Comparison views (16 tests)

### E2E Tests

`jd-optimizer.e2e.test.tsx` includes:

- Complete optimization workflow
- Error state handling
- Editing flow
- Before/after comparison
- Multiple issue fixes
- Input validation
- Animation verification
- View mode toggles
- Accessibility checks

### API Route Tests

`jd-optimizer.test.ts` (20+ tests):

- Input validation
- Error handling
- Response format verification
- Issue detection
- Score calculation
- Edge cases

## Running Tests

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch

# E2E tests specifically
npm test -- e2e

# API tests specifically
npm test -- api/jd-optimizer
```

## Test Coverage

The test suite covers:
- ✅ Component rendering
- ✅ User interactions
- ✅ State management
- ✅ API integration
- ✅ Error handling
- ✅ Animation behavior
- ✅ Accessibility
- ✅ Edge cases
- ✅ File uploads
- ✅ Text editing
- ✅ Progress tracking
- ✅ Before/after comparison

## State Management

The JDOptimizer component manages:

```tsx
type Step = 'input' | 'processing' | 'results';

state = {
  step: Step,
  originalJD: string,
  optimizedJD: string,
  qualityScore: number,
  issues: OptimizationIssue[],
  loading: boolean,
  error: string | null,
  selectedIssueId: string | null,
  isEditingJD: boolean,
  editedJD: string
}
```

## Features Details

### Quality Score Gauge

- Animated progress from 0-100
- Color-coded feedback (red/orange/yellow/green)
- Quality rating labels
- Performance messages

### Issue Cards

- Expandable/collapsible detail view
- Severity badges (High/Medium/Low)
- Category badges (Clarity/Tone/etc.)
- Before/after text comparison
- Explanation and impact statements
- Apply fix functionality

### Progress Indicator

- Progress bar with percentage
- 3-phase progress tracking
- Issue resolution stats
- Remaining issues counter

### Before/After Comparison

- Split view (side-by-side)
- Stacked view (responsive)
- Copy to clipboard
- Line/character counts
- Improvement statistics

### Inline Editor

- Full-featured text editor
- Word and character count
- Unsaved changes indicator
- Save/Cancel buttons

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Modern mobile browsers

## Accessibility

- ARIA labels on all inputs
- Keyboard navigation support
- Screen reader friendly
- Color-blind safe color palette
- Sufficient contrast ratios
- Focus management

## Performance

- Lazy loading of components
- Memoized callbacks
- Efficient re-rendering
- Optimized animations
- File upload streaming

## Configuration

The component can be customized via:

```tsx
<JDOptimizer
  apiEndpoint="/api/custom-endpoint"
/>
```

## Integration with Backend

The backend API endpoint should:
1. Accept POST requests with `jobDescription`
2. Validate input (required, length limits)
3. Analyze the job description
4. Return structured optimization results
5. Handle errors gracefully

See `/src/app/api/jd-optimizer/route.ts` for the mock implementation.

## Future Enhancements

- [ ] Real-time suggestions as user types
- [ ] Template-based JD generation
- [ ] Industry-specific analysis
- [ ] Bias detection and removal
- [ ] Multilingual support
- [ ] A/B testing different variations
- [ ] Historical version tracking
- [ ] Team collaboration features
- [ ] Integration with ATS systems
- [ ] SEO optimization for job boards

## Troubleshooting

### API not responding
- Check endpoint URL
- Verify CORS settings
- Check browser console for errors

### Animation not smooth
- Check browser performance
- Verify requestAnimationFrame support
- Check for conflicting CSS

### File upload not working
- Check file type support
- Verify FileReader API support
- Check file size limits

## Development

### Adding a new issue category

1. Update `OptimizationIssue` type in `/src/types/jd-optimizer.ts`
2. Add color handling in relevant components
3. Update API to detect new category
4. Add tests for new category

### Customizing styles

Edit TailwindCSS classes in component files. All classes are documented for easy modification.

### Extending functionality

The component uses React hooks and is fully composable. Each sub-component is independent and can be used separately.

## License

Part of the TrueMatch recruitment platform.
