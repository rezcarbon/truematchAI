# Copy R2 Integration Files to React Project

Your 20,853 Pokémon card images are **live in R2**. Now integrate them into your React app!

---

## 📋 Files to Copy

### Source (Already Generated)
```
~/Documents/
├── r2FilenameMap.ts        ← Card ID → R2 filename mapping (13,605 cards)
├── useCardImage.ts         ← React hook to load images
├── CardGrid.tsx            ← Responsive card grid component
└── CardGrid.css            ← Grid styling
```

### Destination (Your React Project)
```
src/
├── data/
│   └── r2FilenameMap.ts    ← Paste r2FilenameMap.ts here
├── hooks/
│   └── useCardImage.ts     ← Paste useCardImage.ts here
└── components/
    ├── CardGrid.tsx        ← Paste CardGrid.tsx here
    └── CardGrid.css        ← Paste CardGrid.css here
```

---

## 🚀 Step-by-Step

### 1. Create Directories (if they don't exist)
```bash
mkdir -p src/data
mkdir -p src/hooks
mkdir -p src/components
```

### 2. Copy Files

**Option A: Manual Copy-Paste**
```bash
# Open each file and copy contents to your project:
cat ~/Documents/r2FilenameMap.ts     # Copy to src/data/r2FilenameMap.ts
cat ~/Documents/useCardImage.ts      # Copy to src/hooks/useCardImage.ts
cat ~/Documents/CardGrid.tsx         # Copy to src/components/CardGrid.tsx
cat ~/Documents/CardGrid.css         # Copy to src/components/CardGrid.css
```

**Option B: Automated Copy**
```bash
# From your project root directory:
cp ~/Documents/r2FilenameMap.ts src/data/
cp ~/Documents/useCardImage.ts src/hooks/
cp ~/Documents/CardGrid.tsx src/components/
cp ~/Documents/CardGrid.css src/components/
```

---

## 🎯 Quick Integration Test

After copying files, create a test page:

### Test Page (src/pages/CardShowcase.tsx)
```typescript
import React, { useState } from 'react';
import { CardGrid } from '../components/CardGrid';
import { r2FilenameMap, R2_SET_CODES } from '../data/r2FilenameMap';

export function CardShowcase() {
  // Sample cards from R2
  const sampleCards = [
    { id: 'sv3-5-001', name: 'Card 001', set: 'Scarlet & Violet 3.5' },
    { id: 'sv3-5-002', name: 'Card 002', set: 'Scarlet & Violet 3.5' },
    { id: 'sv3-5-003', name: 'Card 003', set: 'Scarlet & Violet 3.5' },
    { id: 'xy2-055', name: 'Card 055', set: 'XY2' },
    { id: 'me4-001', name: 'Card 001', set: 'Chaos Rising' },
  ];

  return (
    <div>
      <h1>Pokémon TCG Marketplace</h1>
      <p>
        ✅ {Object.keys(r2FilenameMap).length} cards available from R2<br/>
        🏷️ {R2_SET_CODES.length} unique sets
      </p>
      <CardGrid cards={sampleCards} columns={4} />
    </div>
  );
}
```

### Import in App.tsx
```typescript
import { CardShowcase } from './pages/CardShowcase';

export default function App() {
  return <CardShowcase />;
}
```

---

## ✅ Verify Images Load from R2

### 1. Check Browser DevTools
- Open DevTools → Network tab
- Look for requests to `pokemontcg.r2.cloudflarestorage.com`
- Should see: `200 OK` responses

### 2. Check Image Sources
```typescript
import { useCardImage } from './hooks/useCardImage';

function DebugCard() {
  const url = useCardImage('sv3-5-001');
  return (
    <div>
      <img src={url} alt="test" />
      <p>Image URL: {url}</p>
    </div>
  );
}
```

Look for: `https://pokemontcg.r2.cloudflarestorage.com/Pokemon%20TCG/...`

### 3. Check Map
```typescript
import { r2FilenameMap, getR2ImageUrl } from './data/r2FilenameMap';

// In your browser console:
// getR2ImageUrl('sv3-5-001')
// Should return: https://pokemontcg.r2.cloudflarestorage.com/Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_001_std.jpg
```

---

## 🧪 Test Different Card Sets

These card IDs are confirmed in R2:

```typescript
// Scarlet & Violet 3.5
'sv3-5-001'
'sv3-5-050'
'sv3-5-100'

// Scarlet & Violet 9
'sv9-001'
'sv9-050'

// XY2
'xy2-055'
'xy2-100'

// Sword & Shield
'swsh1-001'
'swsh2-050'

// Chaos Rising
'me4-001'
'me4-050'
```

---

## 🔄 Update Mapping (If Needed)

If you add more images to R2 later:

```bash
# Regenerate the mapping
cd ~/Documents
node generate-r2-map-complete.js

# Copy updated file
cp r2FilenameMap.ts /path/to/your/project/src/data/
```

---

## 📊 What's Mapped

- **Total in R2:** 20,853 image files
- **Mapped card IDs:** 13,605
- **Unmapped cards:** Will fall back to pokemontcg.io
- **Set codes:** 120 unique sets

---

## 🎨 Customize CardGrid

```typescript
<CardGrid
  cards={cards}
  columns={6}              // 6 columns instead of 4
  onCardClick={(card) => {
    console.log('Card clicked:', card.id);
    // Show details, add to cart, etc.
  }}
/>
```

---

## 💡 Example: Display All Cards from a Set

```typescript
import { r2FilenameMap } from './data/r2FilenameMap';

function ViewSet({ setCode }) {
  const cardsInSet = Object.entries(r2FilenameMap)
    .filter(([id]) => id.startsWith(`${setCode}-`))
    .map(([id]) => ({
      id,
      name: id,
      set: setCode,
    }));

  return (
    <div>
      <h2>{setCode} - {cardsInSet.length} cards</h2>
      <CardGrid cards={cardsInSet} />
    </div>
  );
}

// Usage: <ViewSet setCode="sv3-5" />
// Shows all 50+ cards from Scarlet & Violet 3.5
```

---

## ✨ Production Checklist

- [ ] Copy all 4 files to React project
- [ ] Update imports in your components
- [ ] Test image loading in browser
- [ ] Verify Network tab shows R2 URLs
- [ ] Test on mobile (responsive layout)
- [ ] Deploy to staging/production
- [ ] Monitor R2 CDN performance
- [ ] Add error handling for missing images

---

## 🆘 Troubleshooting

**Images show 404 (not found)**
- Check DevTools → Network tab
- Verify card ID is in `r2FilenameMap`
- Try a known card: `sv3-5-001`

**Images fall back to pokemontcg.io**
- Card ID may not be in R2 mapping (only 13,605 of 20,853 mapped)
- Check if filename pattern matches
- Regenerate mapping if you added new images

**Slow loading**
- First load from region is ~200ms (R2 → Cloudflare CDN)
- Subsequent loads use cache (<50ms)
- This is normal!

**CORS errors**
- Shouldn't happen for image loading
- If fetching JSON, use `no-cors` or proxy through backend

---

## ✅ You're Ready!

All 20,853 images are live in R2.  
13,605 are mapped and ready to use.  
Copy the files and start building! 🚀

---

**Files location:** `~/Documents/`  
**R2 Bucket:** pokemontcg  
**Image URL format:** `https://pokemontcg.r2.cloudflarestorage.com/{encoded-path}`
