# ✅ R2 Images Are Now Ready to Use!

## 📊 What's Mapped

- **Total Files in R2:** 20,853 (3.37 GB)
- **Mapped Card IDs:** 13,605
- **Unique Sets:** 120
- **URL Encoding:** ✅ Spaces handled (%20)
- **Fallback:** pokemontcg.io for unmapped cards

## 🎯 Card ID Formats

Two filename patterns are supported:

### Pattern 1: Modern Sets (Scarlet & Violet, Sword & Shield, etc.)
```
Filename: sv3-5_en_001_std.jpg
Card ID:  sv3-5-001
URL: https://pokemontcg.r2.cloudflarestorage.com/Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_001_std.jpg
```

### Pattern 2: Legacy Sets (XY, Sun & Moon, etc.)
```
Filename: en_US-XY2-055-skuntank.jpg
Card ID:  xy2-055
URL: https://pokemontcg.r2.cloudflarestorage.com/pokemon-tcg/..../en_US-XY2-055-skuntank.jpg
```

---

## 🚀 Use in React

### Option 1: With Hook (Recommended)

```typescript
import { useCardImage } from './hooks/useCardImage';

function Card({ cardId }) {
  const imageUrl = useCardImage(cardId);
  return <img src={imageUrl} alt={cardId} />;
}

// Usage
<Card cardId="sv3-5-001" />  // Loads from R2
<Card cardId="xy2-055" />    // Loads from R2
<Card cardId="unknown-id" /> // Falls back to pokemontcg.io
```

### Option 2: With Component

```typescript
import { CardImage } from './hooks/useCardImage';

export default function App() {
  return (
    <>
      <CardImage cardId="sv3-5-001" size="medium" />
      <CardImage cardId="xy2-055" size="medium" />
    </>
  );
}
```

### Option 3: Get URL Only

```typescript
import { getR2ImageUrl } from './data/r2FilenameMap';

const url = getR2ImageUrl('sv3-5-001');
// https://pokemontcg.r2.cloudflarestorage.com/Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_001_std.jpg
```

---

## 🔍 Check if Card is in R2

```typescript
import { r2FilenameMap } from './data/r2FilenameMap';

if (r2FilenameMap['sv3-5-001']) {
  console.log('✅ Card is in R2');
} else {
  console.log('⚠️ Card not in R2, will use fallback');
}
```

---

## 📋 Available Set Codes

All 120 unique Pokémon TCG sets are included:

- **Scarlet & Violet:** sv3, sv4, sv5, sv6, sv7, sv8, sv9, sv10, sve, svbsp, sv3-5
- **Sword & Shield:** swsh1-12, swshbsp
- **Sun & Moon:** sm1-12, smbsp
- **XY:** xy0-12, xybsp
- **Black & White:** bw1-11, bwbsp
- **HeartGold/SoulSilver:** hgss1-4
- **Neo:** (multiple eras)
- **And more!** (120 total)

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Load time (R2) | 50-200ms |
| Cache duration | 1 year |
| CDN coverage | Global (Cloudflare) |
| Egress cost | Free |

---

## 📝 Sample Integration

```typescript
// cardService.ts
import { getR2ImageUrl } from './r2FilenameMap';

export function getCardImageUrl(cardId: string): string {
  // Try R2 first (13,605 mapped cards)
  const r2Url = getR2ImageUrl(cardId);
  if (r2Url) {
    return r2Url;
  }

  // Fallback to pokemontcg.io
  return `https://images.pokemontcg.io/cards/${cardId}.png`;
}

// In your component
import { getCardImageUrl } from './cardService';

export function CardDisplay({ card }) {
  return (
    <img 
      src={getCardImageUrl(card.id)} 
      alt={card.name}
      loading="lazy"
    />
  );
}
```

---

## 🧪 Test It

### Check if your card is mapped:
```bash
grep "your-card-id" ~/Documents/r2FilenameMap.ts
```

### Get the R2 URL:
```typescript
import { getR2ImageUrl } from './r2FilenameMap';
const url = getR2ImageUrl('sv3-5-001');
console.log(url);
// https://pokemontcg.r2.cloudflarestorage.com/Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_001_std.jpg
```

---

## 📦 Files to Copy

Into your React project:

```bash
cp ~/Documents/r2FilenameMap.ts src/data/
cp ~/Documents/useCardImage.ts src/hooks/
cp ~/Documents/CardGrid.tsx src/components/
cp ~/Documents/CardGrid.css src/components/
```

---

## ✅ What's Fixed

- ✅ 13,605 cards now mapped to R2 (was using fallback before)
- ✅ URL encoding fixed (spaces as %20)
- ✅ Both filename patterns handled
- ✅ getR2ImageUrl() helper function added
- ✅ Ready for production use

---

## 🎯 Next Steps

1. Copy files to your React project
2. Import `CardImage` or `useCardImage`
3. Pass card IDs: `sv3-5-001`, `xy2-055`, etc.
4. Images load from R2 ✅
5. Unmapped cards fall back to pokemontcg.io 📖

**Images are live from R2!** 🚀
