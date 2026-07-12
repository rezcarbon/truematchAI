# Job Search Feature - Quick Start Guide

## Installation & Setup

### 1. Files Created
- 8 React components (TypeScript/TSX)
- 1 matching algorithm utility
- 1 job data module with 8 sample jobs
- 1 favorites management hook
- 3 comprehensive E2E test suites
- 1 dedicated page at `/job-search`

All dependencies already installed: `recharts`, `lucide-react`, `tailwind-css`

### 2. Directory Structure
```
src/
├── types/jobs.ts                      # Types
├── lib/job-data.ts                    # Sample jobs
├── lib/capability-matching.ts         # Matching algorithm
├── hooks/useJobFavorites.ts           # Favorites hook
├── components/job-search/             # All components
└── app/job-search/page.tsx            # Route

__tests__/job-search/                  # Tests
├── job-browser.e2e.test.tsx
├── capability-matching.test.ts
└── job-favorites.test.ts
```

## Running the Feature

### Development
```bash
cd /Users/modvader/Documents/codebase/truematch/web
npm run dev
# Visit http://localhost:3000/job-search
```

### Testing
```bash
# All tests
npm test

# Specific test file
npm test job-browser.e2e.test.tsx

# With coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

## Key Components

### Main Component: JobBrowser
```tsx
<JobBrowser 
  userSkills={[
    { name: 'React', proficiency: 'advanced', yearsOfExperience: 4 },
    { name: 'TypeScript', proficiency: 'advanced', yearsOfExperience: 3 }
  ]}
  yearsOfExperience={5}
/>
```

### Match Score Coloring
```
Score 85+  → Green  (#10b981) → "Excellent Match"
Score 70+  → Blue   (#3b82f6) → "Strong Match"
Score 50+  → Amber  (#f59e0b) → "Partial Match"
Score <50  → Red    (#ef4444) → "Hidden Gem"
```

### Match Breakdown
```typescript
{
  skillsMatch: 85,        // 45% weight
  experienceMatch: 92,    // 25% weight
  roleTransitionScore: 70,// 15% weight
  culturalFitEstimate: 75 // 15% weight
}
```

## Features by Component

### 1. JobBrowser (Main)
- Search & filtering
- Job card grid
- Modal coordination
- Favorites management

### 2. JobCard
- Match score display
- Top 3 skills
- Save button
- Details & Apply buttons

### 3. FilterSidebar
- Salary range
- Match score threshold
- Work mode
- Location, role, level, industry
- Reset button

### 4. MatchScoreDisplay
- Circular progress
- Color-coded
- Auto-sized (sm/md/lg)

### 5. SkillsRadarChart
- 8 top matched skills
- Dual-axis comparison
- Missing skills alert
- Overqualified indicator

### 6. HiddenGemBadge
- Sparkle icon
- Hover tooltip
- Custom reasons

### 7. ApplyModal
- Email input
- Resume selector
- Cover letter/motivation
- Validation & errors
- Success confirmation

### 8. JobDetailsModal
- Full job info
- Match breakdown
- Radar chart
- Responsibilities
- Requirements
- Benefits
- Reasoning

## Data Models

### Skill
```typescript
{
  name: string,
  proficiency: 'beginner' | 'intermediate' | 'advanced' | 'expert',
  yearsOfExperience?: number
}
```

### Job
```typescript
{
  id: string,
  title: string,
  company: string,
  location: string,
  remote: 'fully' | 'hybrid' | 'onsite' | 'flexible',
  salaryMin: number,
  salaryMax: number,
  description: string,
  requirements: JobRequirement[],
  responsibilities: string[],
  benefits: string[],
  yearsOfExperienceRequired: number,
  level: 'entry' | 'mid' | 'senior' | 'lead' | 'executive',
  isHiddenGem?: boolean,
  hiddenGemReason?: string
}
```

### CapabilityMatch
```typescript
{
  score: number (0-100),
  matchType: 'exact' | 'strong' | 'partial' | 'hidden_gem',
  breakdown: {
    skillsMatch: number,
    experienceMatch: number,
    roleTransitionScore: number,
    culturalFitEstimate: number
  },
  reasoning: string[]
}
```

## Using the Hooks

### useJobFavorites
```tsx
const { 
  savedJobs,          // SavedJob[]
  isSaved,            // (jobId) => boolean
  toggleSave,         // (jobId) => Promise<void>
  removeSaved,        // (jobId) => Promise<void>
  updateNotes,        // (jobId, notes) => Promise<void>
  markApplied,        // (jobId) => Promise<void>
  getSavedJob,        // (jobId) => SavedJob | undefined
  isLoading           // boolean
} = useJobFavorites(userId);
```

## Common Tasks

### Add a Custom Job
```typescript
// In src/lib/job-data.ts
const newJob: Job = {
  id: 'custom-job',
  title: 'Your Job Title',
  company: 'Your Company',
  // ... other fields
};

// Add to sampleJobs array
sampleJobs.push(newJob);
```

### Modify Matching Weights
```typescript
// In src/lib/capability-matching.ts
const weights = {
  skillsMatch: 0.45,      // Adjust this
  experienceMatch: 0.25,  // Adjust this
  roleTransition: 0.15,   // Adjust this
  culturalFit: 0.15       // Adjust this
};
```

### Change Color Scheme
```typescript
// In src/lib/capability-matching.ts
function getMatchScoreColor(score: number): string {
  if (score >= 85) return '#YOUR_COLOR'; // Change here
  // ...
}
```

### Connect to Backend
```typescript
// Replace in src/lib/job-data.ts
async function fetchJobs(): Promise<Job[]> {
  const response = await fetch('/api/jobs');
  return response.json();
}
```

## Testing Patterns

### Component Testing
```tsx
const { result } = renderHook(() => useJobFavorites());
await act(async () => {
  await result.current.toggleSave('job-1');
});
expect(result.current.isSaved('job-1')).toBe(true);
```

### Algorithm Testing
```typescript
const match = calculateCapabilityMatch(skills, yearsExp, job);
expect(match.score).toBeGreaterThan(70);
expect(match.matchType).toBe('strong');
```

### UI Testing
```tsx
const user = userEvent.setup();
const searchInput = screen.getByPlaceholderText(/search/i);
await user.type(searchInput, 'React Developer');
```

## Performance Tips

1. **Memoization**: Wrap expensive calculations in useMemo
2. **Lazy Loading**: Modals render only when open
3. **LocalStorage**: Favorites don't require API calls
4. **Chunking**: Show jobs in pagination for large datasets

## Accessibility

- ✅ Semantic HTML (buttons, headings, labels)
- ✅ ARIA labels for icons
- ✅ Keyboard navigation support
- ✅ Color-blind friendly (+ icons with colors)
- ✅ Focus management in modals

## Browser Support

- Chrome/Edge: ✅ Full
- Firefox: ✅ Full
- Safari: ✅ Full
- Mobile (iOS/Android): ✅ Responsive

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Match scores all 0 | Verify skill names match requirements (case-insensitive) |
| Favorites not saving | Check localStorage is enabled in browser |
| Radar chart not showing | Ensure skillsAlignment.matchedSkills has items |
| Tests failing | Run `npm test -- --clearCache` |
| Styles not applying | Rebuild with `npm run build` |

## Environment Variables

No environment variables required for basic functionality.

For backend integration, add to `.env.local`:
```
NEXT_PUBLIC_API_URL=http://your-api.com
```

## API Integration Template

```typescript
// Replace in JobBrowser.tsx
async function fetchEnhancedJobs() {
  const jobs = await fetch('/api/jobs').then(r => r.json());
  return jobs.map(job => ({
    ...job,
    capabilityMatch: calculateCapabilityMatch(userSkills, yearsOfExperience, job)
  }));
}
```

## Next Steps

1. **Customize**: Modify colors, weights, or jobs
2. **Integrate**: Connect to your backend
3. **Deploy**: Build and deploy to production
4. **Monitor**: Track user behavior with analytics
5. **Extend**: Add features like job alerts or skill recommendations

## Code Statistics

| Metric | Value |
|--------|-------|
| Components | 8 |
| Hooks | 1 |
| Utilities | 2 |
| Tests | 3 suites |
| Test Cases | 90+ |
| Lines of Code | ~2000 |
| Sample Jobs | 8 |
| Features | 15+ |

## Support Resources

- **Types**: `/src/types/jobs.ts`
- **Algorithm**: `/src/lib/capability-matching.ts`
- **Tests**: `/__tests__/job-search/`
- **Docs**: `/JOB_SEARCH_FEATURE.md`
- **Page**: `/src/app/job-search/page.tsx`

## Quick Links

- Start dev server: `npm run dev`
- Run tests: `npm test`
- Build: `npm run build`
- Type check: `npm run typecheck`

---

**Ready to use!** Visit `/job-search` to see the feature in action.
