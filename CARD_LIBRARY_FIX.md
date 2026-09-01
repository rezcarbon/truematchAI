# 🎴 Card Library Fix Guide - "The Collective"

## ✅ The Issue: Back-of-Card Images

Your Card Library is showing **back-of-card images** (generic Pokéball) instead of **front-facing card artwork**.

**Proof:** R2 bucket has correct front-facing images ✓  
**Problem:** Card Library is using wrong URLs

---

## 🔧 The Root Cause

### ❌ WRONG (Showing generic Pokéballs)
```javascript
// Using back-of-card endpoint
const url = `https://images.pokemontcg.io/cards/${cardId}_back.png`;
// Result: Shows generic back of card (Pokéball)
```

### ✅ CORRECT (Showing actual card art)
```javascript
// Using front-facing endpoint
const url = `https://images.pokemontcg.io/cards/${cardId}.png`;
// Result: Shows Oddish, Cindermaw, Tidecaller, etc.
```

---

## 🚀 3-Minute Fix

### For React Components:

```jsx
import React from 'react';

function CardImage({ cardId, cardName }) {
  return (
    <img
      src={`https://images.pokemontcg.io/cards/${cardId}.png`}
      alt={cardName}
      onError={(e) => {
        // Fallback if pokemontcg.io temporarily fails
        e.target.src = `https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/Pokemon%20TCG/Pokemon%20TCG/ancient-origins/en_US-XY7-001-oddish.jpg`;
      }}
      style={{ width: '100%', maxWidth: '200px' }}
    />
  );
}

// Usage
<CardImage cardId="xy7-001" cardName="Oddish" />
```

### For Vue Components:

```vue
<template>
  <img
    :src="`https://images.pokemontcg.io/cards/${cardId}.png`"
    :alt="cardName"
    @error="fallbackToR2"
    style="width: 100%; max-width: 200px"
  />
</template>

<script>
export default {
  props: ['cardId', 'cardName'],
  methods: {
    fallbackToR2(event) {
      event.target.src = `https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/Pokemon%20TCG/Pokemon%20TCG/ancient-origins/en_US-XY7-001-oddish.jpg`;
    }
  }
}
</script>
```

### For Plain HTML:

```html
<img
  id="card-image"
  src="https://images.pokemontcg.io/cards/xy7-001.png"
  alt="Oddish"
  onerror="this.src='https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/Pokemon%20TCG/Pokemon%20TCG/ancient-origins/en_US-XY7-001-oddish.jpg'"
/>
```

---

## 📋 Card ID Format Check

Your Card Library must use **correct card IDs**:

| Set | Card ID | Example |
|-----|---------|---------|
| Ancient Origins | `xy7-001` | Oddish |
| Ascended Heroes | `me2-5-001` | Card 001 |
| Chaos Rising | `me4-001` | Card 001 |
| Perfect Order | `me3-001` | Card 001 |

❌ **Wrong:** `oddish`, `001`, `ash`, `charizard-001`  
✅ **Correct:** `xy7-001`, `me2-5-001`, `me4-001`

---

## 🧪 Test URLs (Copy & Paste)

These should show **actual card artwork** (not Pokéballs):

| Card | Front-Facing URL |
|------|-----------------|
| Oddish | https://images.pokemontcg.io/cards/xy7-001.png |
| Gloom | https://images.pokemontcg.io/cards/xy7-002.png |
| Spinarak | https://images.pokemontcg.io/cards/xy7-005.png |

If these show Pokéballs in your browser, check:
1. Are you using `_back.png` in the URL? → Remove it
2. Is pokemontcg.io down? → Use R2 URL instead
3. Wrong card ID format? → Use `set-number` format

---

## 🎯 Integration Steps

1. **Find your Card component** in "The Collective" codebase
2. **Replace the image URL** with: `https://images.pokemontcg.io/cards/${cardId}.png`
3. **Remove any `_back` suffix** from URLs
4. **Test with card IDs:**
   - xy7-001 (should show Oddish)
   - xy7-002 (should show Gloom)
   - xy7-005 (should show Spinarak)
5. **Deploy** ✅

---

## 📊 Before & After

### BEFORE (Generic Pokéball)
```
┌─────────────────┐
│   [Pokéball]    │  ❌ Wrong URL
│   Emberling     │  Using _back.png
└─────────────────┘
```

### AFTER (Real Card Art)
```
┌─────────────────┐
│  [Card Artwork] │  ✅ Correct URL
│   Emberling     │  Using .png
└─────────────────┘
```

---

## 🔗 URLs Reference

### ✅ Front-Facing (What you want)
```
https://images.pokemontcg.io/cards/{cardId}.png
```

### ❌ Back-of-Card (What you DON'T want)
```
https://images.pokemontcg.io/cards/{cardId}_back.png
```

### 📦 R2 CDN (Fast fallback)
```
https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/Pokemon%20TCG/Pokemon%20TCG/{set-name}/{filename}
```

---

## ✨ Next Steps

After fixing the Card Library:

1. ✅ Cards display with proper artwork
2. ✅ Test all card sets (Ancient Origins, Ascended Heroes, etc.)
3. ✅ Monitor R2 CDN for fallback performance
4. ✅ Deploy to production
5. ✅ Celebrate! 🎉

**Estimated fix time: 5-10 minutes** (find & replace URLs)

---

**Questions?** Check the URL in your browser's network tab to see what's actually being requested.
