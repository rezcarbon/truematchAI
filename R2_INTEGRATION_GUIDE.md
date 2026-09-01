# 🔗 Pokémon TCG R2 CDN Integration Guide

## Quick Links & Integration Methods

**Last Updated**: July 17, 2026  
**Status**: ✅ Production Ready  
**Cards Available**: 14,286

---

## 📌 Essential Information

### R2 Public URL
```
https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/
```

### Card Mapping File
```
~/Documents/r2-auto-discovered-mapping.json
```

### Fallback URL (if R2 fails)
```
https://images.pokemontcg.io/cards
```

---

## 🎯 Integration Options

### Option 1: Direct R2 Public URL (Simplest)

Use the base URL directly in your HTML:

```
https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/
```

**Example card URLs:**
```
https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/Pokemon%20TCG/Pokemon%20TCG/ancient-origins/en_US-XY7-001-oddish.jpg

https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/ascended-heroes/me2-5_en_001_std.jpg

https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/chaos-rising/me4_en_001_std.jpg

https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/perfect-order/me3_en_001_std.jpg
```

---

### Option 2: JavaScript Integration with Mapping

Load the complete card mapping and construct URLs programmatically:

```javascript
// Load the mapping
const mapping = await fetch(
  'file:///Users/modvader/Documents/r2-auto-discovered-mapping.json'
).then(r => r.json());

// Configuration
const R2_PUBLIC_URL = 'https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev';
const FALLBACK_URL = 'https://images.pokemontcg.io/cards';

// Get card URL
function getCardUrl(cardId) {
  const card = mapping[cardId];
  if (!card) return `${FALLBACK_URL}/${cardId}.png`;
  return `${R2_PUBLIC_URL}/${card.path}/${card.filename}`;
}

// Usage
const url = getCardUrl('xy7-001');
console.log(url);
```

---

### Option 3: React Component

Create a reusable React component for card images:

```jsx
import { useMemo } from 'react';
import cardMapping from './data/cards.json';

const PokemonCard = ({ cardId, onError }) => {
  const R2_URL = 'https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev';
  const FALLBACK_URL = 'https://images.pokemontcg.io/cards';
  
  const imageUrl = useMemo(() => {
    const card = cardMapping[cardId];
    return card ? `${R2_URL}/${card.path}/${card.filename}` : `${FALLBACK_URL}/${cardId}.png`;
  }, [cardId]);

  return (
    <img 
      src={imageUrl} 
      alt={cardId}
      loading="lazy"
      onError={(e) => {
        if (e.target.src !== `${FALLBACK_URL}/${cardId}.png`) {
          e.target.src = `${FALLBACK_URL}/${cardId}.png`;
        }
        onError?.(e);
      }}
      style={{ width: '100%', height: 'auto' }}
    />
  );
};

export default PokemonCard;
```

**Usage:**
```jsx
<PokemonCard cardId="xy7-001" />
<PokemonCard cardId="me2-5-001" />
```

---

### Option 4: Copy Mapping to Your Project

```bash
cp ~/Documents/r2-auto-discovered-mapping.json /your/project/data/cards.json
```

```javascript
import cardMapping from './data/cards.json';

const R2_URL = 'https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev';
const FALLBACK_URL = 'https://images.pokemontcg.io/cards';

function getCardImageUrl(cardId) {
  const card = cardMapping[cardId];
  if (!card) return `${FALLBACK_URL}/${cardId}.png`;
  return `${R2_URL}/${card.path}/${card.filename}`;
}
```

---

### Option 5: HTML Image Tags (Direct)

```html
<!-- Single card -->
<img 
  src="https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/Pokemon%20TCG/Pokemon%20TCG/ancient-origins/en_US-XY7-001-oddish.jpg" 
  alt="Oddish"
  loading="lazy"
/>

<!-- With fallback -->
<img 
  src="https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/Pokemon%20TCG/Pokemon%20TCG/ancient-origins/en_US-XY7-001-oddish.jpg" 
  onerror="this.src='https://images.pokemontcg.io/cards/xy7-001.png'"
  alt="Oddish"
/>

<!-- Card grid -->
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
  <img src="https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/Pokemon%20TCG/Pokemon%20TCG/ancient-origins/en_US-XY7-001-oddish.jpg" alt="Card 1" loading="lazy" />
  <img src="https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/Pokemon%20TCG/Pokemon%20TCG/ancient-origins/en_US-XY7-002-gloom.jpg" alt="Card 2" loading="lazy" />
</div>
```

---

### Option 6: Vue Component

```vue
<template>
  <img 
    :src="cardImageUrl" 
    :alt="cardId"
    @error="handleError"
    class="pokemon-card"
    loading="lazy"
  />
</template>

<script>
import cardMapping from './data/cards.json';

export default {
  props: {
    cardId: { type: String, required: true }
  },
  data() {
    return {
      R2_URL: 'https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev',
      FALLBACK_URL: 'https://images.pokemontcg.io/cards'
    };
  },
  computed: {
    cardImageUrl() {
      const card = cardMapping[this.cardId];
      if (!card) return `${this.FALLBACK_URL}/${this.cardId}.png`;
      return `${this.R2_URL}/${card.path}/${card.filename}`;
    }
  },
  methods: {
    handleError(event) {
      const fallbackUrl = `${this.FALLBACK_URL}/${this.cardId}.png`;
      if (event.target.src !== fallbackUrl) {
        event.target.src = fallbackUrl;
      }
    }
  }
};
</script>
```

---

### Option 7: Quick HTML Prototype

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pokémon TCG Cards</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
    .container { max-width: 1200px; margin: 0 auto; }
    h1 { text-align: center; margin-bottom: 40px; color: #333; }
    .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
    .card { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.3s; }
    .card:hover { transform: translateY(-4px); }
    .card img { width: 100%; height: auto; display: block; }
    .card-info { padding: 12px; text-align: center; font-size: 14px; color: #666; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🎴 Pokémon TCG Cards</h1>
    <div class="card-grid" id="gallery"></div>
  </div>

  <script>
    const R2_URL = 'https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev';
    const FALLBACK_URL = 'https://images.pokemontcg.io/cards';
    
    const CARDS = [
      { id: 'xy7-001', path: 'Pokemon%20TCG/Pokemon%20TCG/ancient-origins', file: 'en_US-XY7-001-oddish.jpg', name: 'Oddish' },
      { id: 'xy7-002', path: 'Pokemon%20TCG/Pokemon%20TCG/ancient-origins', file: 'en_US-XY7-002-gloom.jpg', name: 'Gloom' },
      { id: 'me2-5-001', path: 'ascended-heroes', file: 'me2-5_en_001_std.jpg', name: 'Ascended Heroes 001' },
      { id: 'me4-001', path: 'chaos-rising', file: 'me4_en_001_std.jpg', name: 'Chaos Rising 001' },
    ];

    const gallery = document.getElementById('gallery');

    CARDS.forEach(card => {
      const cardUrl = `${R2_URL}/${card.path}/${card.file}`;
      const fallbackUrl = `${FALLBACK_URL}/${card.id}.png`;
      
      const cardEl = document.createElement('div');
      cardEl.className = 'card';
      cardEl.innerHTML = `
        <img src="${cardUrl}" alt="${card.name}" onerror="this.src='${fallbackUrl}'" loading="lazy" />
        <div class="card-info">${card.name}</div>
      `;
      gallery.appendChild(cardEl);
    });
  </script>
</body>
</html>
```

---

## 📊 Card Path Examples by Pattern

### en_US-NAME Pattern (9,851 cards)
```
en_US-XY7-001-oddish.jpg
en_US-XY7-002-gloom.jpg
en_US-Ann25th-001-ho_oh.jpg
```

### std.jpg Pattern (3,748 cards)
```
me2-5_en_001_std.jpg
me4_en_001_std.jpg
me3_en_001_std.jpg
```

### en.jpg Pattern (687 cards)
```
xy7_en_001.jpg
xy7_en_002.jpg
```

---

## 📋 Sample Card IDs

```javascript
const SAMPLE_CARDS = [
  // Ancient Origins
  'xy7-001', 'xy7-002', 'xy7-003', 'xy7-004', 'xy7-005', 'xy7-006',
  
  // Ascended Heroes
  'me2-5-001', 'me2-5-002', 'me2-5-003',
  
  // Chaos Rising
  'me4-001', 'me4-002', 'me4-003',
  
  // Perfect Order
  'me3-001', 'me3-002', 'me3-003',
  
  // Anniversary 25th
  'ann25th-001', 'ann25th-002', 'ann25th-003',
  
  // And 14,281 more...
];
```

---

## ✅ Which Option Should You Use?

| Option | Best For | Setup Time |
|--------|----------|-----------|
| **Option 1** | Static HTML, simple images | 1 minute |
| **Option 2** | JavaScript projects | 5 minutes |
| **Option 3** | React apps | 10 minutes |
| **Option 4** | Large projects | 5 minutes |
| **Option 5** | Quick prototypes | 1 minute |
| **Option 6** | Vue apps | 10 minutes |
| **Option 7** | Full prototype | 2 minutes |

---

## 🎯 Configuration Summary

```javascript
const POKEMON_TCG_CONFIG = {
  R2_PUBLIC_URL: 'https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev',
  FALLBACK_URL: 'https://images.pokemontcg.io/cards',
  MAPPING_FILE: '~/Documents/r2-auto-discovered-mapping.json',
  TOTAL_CARDS: 14286,
};
```

---

## 🔒 Best Practices

1. ✅ Always use HTTPS - All R2 URLs are HTTPS
2. ✅ Add fallback - Implement error handlers
3. ✅ Lazy load - Use `loading="lazy"` on img tags
4. ✅ Cache headers - R2 returns 1-year cache headers
5. ✅ Error handling - Implement onerror handlers
6. ✅ Monitor - Check Cloudflare dashboard regularly

---

## 🚀 Performance Tips

```html
<!-- Lazy loading -->
<img src="..." loading="lazy" alt="Card" />

<!-- With dimensions to prevent layout shift -->
<img src="..." width="200" height="280" alt="Card" />

<!-- Preload critical cards -->
<link rel="preload" as="image" href="...">
```

---

## 📚 Files Reference

- **Mapping**: `~/Documents/r2-auto-discovered-mapping.json`
- **Production HTML**: `~/Documents/pokemon-r2-production.html`
- **Auto-scan script**: `~/Documents/auto-scan-r2-complete.js`

---

**Status**: ✅ Production Ready | **Cards**: 14,286 | **Last Updated**: July 17, 2026
