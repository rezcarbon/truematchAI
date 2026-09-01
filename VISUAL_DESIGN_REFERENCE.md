# TrueMatch AI-Native Platform
## Visual Design System Reference Card

**Created:** June 9, 2026  
**Status:** Ready for Implementation  
**Platform:** Next.js 14 + React 18 + Tailwind CSS 3

---

## 🎨 Color Palette

### Primary Colors
| Name | Hex | Usage | Tailwind |
|------|-----|-------|----------|
| Primary Blue | `#0066CC` | Headings, primary buttons, accents | `primary-blue` |
| Accent Cyan | `#00D9FF` | AI highlights, real-time actions, badges | `accent-cyan` |
| Dark Navy | `#1E3A5F` | Cards, panels, dark backgrounds | `dark-navy` |
| Dark Darker | `#0F1E2E` | Page background, deepest background | `dark-darker` |
| Off-white | `#F5F5F5` | Text on dark, contrast elements | `bg-light` |

### Status & Semantic Colors
| Status | Hex | Usage | Tailwind |
|--------|-----|-------|----------|
| Success | `#10B981` | AI approved, governance passed ✓ | `status-success` |
| Warning | `#F59E0B` | Needs review, borderline confidence | `status-warning` |
| Error | `#EF4444` | Governance failed, action blocked ✗ | `status-error` |
| Info | `#00D9FF` | Processing, real-time action | `status-info` |

---

## 🧩 Component Library

### 1. AIConfidenceBadge
**Purpose:** Display AI decision confidence with visual weight  
**Props:** `score: number (0-100)`, `size?: 'sm' | 'md' | 'lg'`

**Behavior:**
- Score 90-100: Green ✓ badge
- Score 70-89: Amber ? badge
- Score <70: Red ! badge

**Example Usage:**
```tsx
<AIConfidenceBadge score={87} size="md" />
// Renders: "? 87%" in amber badge
```

---

### 2. GovernanceGates
**Purpose:** Show which AI governance gates a decision passed  
**Props:** `gates: Gate[]` where Gate has `name`, `passed: boolean`, `timestamp?`

**Gate Types:**
- `coherence` — Does the decision make logical sense?
- `consistency` — Does it align with past decisions?
- `fidelity` — Does it match user patterns?
- `counterrec` — Are counter-recommendations considered?

**Example Usage:**
```tsx
<GovernanceGates gates={[
  { name: 'coherence', passed: true },
  { name: 'consistency', passed: true },
  { name: 'fidelity', passed: false }
]} />
// Renders: [✓ Coherence] [✓ Consistency] [✗ Fidelity]
```

---

### 3. ActionStatusIndicator
**Purpose:** Display current state of autonomous actions  
**Props:** `status: 'pending' | 'executing' | 'completed' | 'failed'`, `progress?: number`, `message?: string`

**Visual Encoding:**
- **Pending:** Yellow clock icon with rotation animation
- **Executing:** Cyan progress bar with % complete
- **Completed:** Green checkmark with timestamp
- **Failed:** Red X with error message tooltip

**Example Usage:**
```tsx
<ActionStatusIndicator status="executing" progress={65} />
// Renders: Cyan bar at 65% width
```

---

### 4. BudgetMeter
**Purpose:** Real-time display of daily budget spent  
**Props:** `spent: number`, `limit: number`, `currency?: string`

**Color Encoding:**
- 0-70%: Green (safe)
- 70-85%: Amber (caution)
- 85-100%: Red (limit approaching)

**Example Usage:**
```tsx
<BudgetMeter spent={450} limit={2000} currency="$" />
// Renders: "$450 / $2000" with green progress bar at 22%
```

---

### 5. CandidateCard
**Purpose:** Display candidate with AI scoring and governance state  
**Props:** Full candidate object with scores, gates, actions

**Layout:**
```
[Avatar] [Name]          [Match % Badge - green/amber/red]
                         [Confidence icon]
[AI-Extracted Skills in cyan tags]
[Gate badges: ✓ Coherence ✓ Consistency ✗ Fidelity ✓ CounterRec]
[Action status: ● Pending / ✓ Completed / ✗ Failed]
[Quick Action Buttons: Approve | Schedule | Archive]
```

---

### 6. ActionTimeline
**Purpose:** Show progression of an action through execution steps  
**Props:** `actions: ActionStep[]` where ActionStep has `type`, `status`, `timestamp`, `actor`

**Visual:**
```
1. Analyzed (2 hrs ago) ✓
   ↓
2. Ranked (2 hrs ago) ✓
   ↓
3. Scheduled Interview (pending) ⏳
   ↓
4. Approved (blocked) ✗
```

---

### 7. AutonomousActionLog
**Purpose:** Real-time feed of system actions (new screen)  
**Features:**
- Live updates every 2 seconds
- Filter: [All] [Pending] [In Progress] [Completed] [Failed]
- Expandable details (JSON, governance gates, cost)
- Right sidebar with summary stats

---

## 🎯 Layout Patterns

### Desktop (1024px+)
```
┌─ Top Nav (dark-navy) ──────────┐
│  Logo | Search | Budget Meter $ │
├──────────────────────────────────┤
│            Dashboard            │
│  ┌──── Left ─────┬─── Right ───┐│
│  │ Candidate     │ Detail       ││
│  │ List          │ Profile      ││
│  │ (sorted by    │ + AI Analy   ││
│  │  AI score)    │ + Gates      ││
│  │               │ + Timeline   ││
│  └───────────────┴──────────────┘│
└──────────────────────────────────┘
```

### Tablet (768px - 1023px)
```
┌─ Top Nav + Hamburger ─────┐
├───────────────────────────┤
│  [List] [Detail] Tabs     │
├───────────────────────────┤
│  Candidate List Stack View│
│  (swipe to detail)        │
└───────────────────────────┘
```

### Mobile (< 768px)
```
┌─ Top Nav ─────────────┐
├───────────────────────┤
│ Candidate List        │
│ (Single column, full) │
├───────────────────────┤
│ Bottom Tab Navigation │
│ [List][Detail][More]  │
└───────────────────────┘
```

---

## 📁 File Structure

```
web/
├── app/
│   ├── globals.css              ← CSS custom properties
│   ├── layout.tsx               ← Add className="dark"
│   └── ...
├── components/
│   ├── ui/
│   │   ├── AIConfidenceBadge.tsx        ← NEW
│   │   ├── GovernanceGates.tsx          ← NEW
│   │   ├── ActionStatusIndicator.tsx    ← NEW
│   │   ├── BudgetMeter.tsx              ← NEW
│   │   ├── CandidateCard.tsx            ← ENHANCE
│   │   └── ActionTimeline.tsx           ← NEW
│   └── dashboard/
│       ├── RecruiterDashboard.tsx       ← ENHANCE
│       ├── CandidateDetail.tsx          ← ENHANCE
│       ├── AdminControlPanel.tsx        ← ENHANCE
│       └── AutonomousActionLog.tsx      ← NEW
├── tailwind.config.js           ← Update colors
└── ...
```

---

## 🚀 Implementation Roadmap

| Week | Task | Files |
|------|------|-------|
| 1 | Theme & colors | tailwind.config.js, globals.css, layout.tsx |
| 1-2 | Build components | ui/*.tsx (all 6 components) |
| 2 | Update dashboards | RecruiterDashboard, CandidateDetail |
| 3 | Action log + admin | AutonomousActionLog, AdminControlPanel |
| 4 | Responsive & polish | All files, accessibility audit |

---

## ✅ Testing Checklist

- [ ] Dark background applied across all pages
- [ ] Cyan accents visible on interactive elements
- [ ] Confidence badges show correct color (green/amber/red)
- [ ] Governance gates render with icons and colors
- [ ] Budget meter updates in real-time
- [ ] Action timeline displays vertically/horizontally
- [ ] Responsive: Renders correctly at 1920px, 1024px, 768px, 375px
- [ ] Accessibility: All badges have labels, keyboard nav works, color + icons
- [ ] Performance: No layout shifts, smooth animations
- [ ] Production: No console errors, optimized images

---

## 🎨 Quick CSS Classes

Use these Tailwind utilities throughout components:

```css
/* Backgrounds */
.bg-dark-darker       /* Page background */
.bg-dark-navy         /* Cards/panels */

/* Text */
.text-accent-cyan     /* AI highlights */
.text-primary-blue    /* Links/headings */
.text-white           /* Primary text */

/* Buttons */
.bg-primary-blue      /* Primary buttons */
.bg-accent-cyan       /* AI action buttons */
.bg-status-success    /* Approve */
.bg-status-warning    /* Review */
.bg-status-error      /* Reject/blocked */

/* Badges */
.rounded-full         /* Pill-shaped */
.px-3 .py-1.5         /* Badge padding */

/* Effects */
.transition-all       /* Smooth color transitions */
.duration-300         /* 300ms animation */
.animate-spin         /* Rotating icons (pending) */
```

---

## 🔗 References

- **Design System:** TrueMatch_Visual_Design_System.docx
- **Implementation Guide:** TrueMatch_Implementation_Quick_Start.docx
- **Figma** (if available): [Link to Figma design]

---

## 📝 Notes for Developers

1. **Use CSS custom properties** for any dynamic color changes (theme switching)
2. **Always pair colors with icons/text** — don't rely on color alone for accessibility
3. **Test on real devices** — simulators don't always match actual rendering
4. **Monitor performance** — cyan animations should be 60fps (use `will-change` sparingly)
5. **Document deviations** — If you deviate from this spec, update this file

---

**Last Updated:** June 9, 2026  
**Next Review:** After first implementation sprint  
**Questions?** Check the full design system document or consult with the design team.
