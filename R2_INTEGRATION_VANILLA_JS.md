# R2 Integration for Vanilla HTML/JavaScript

If your prototype is plain **HTML/CSS/JavaScript** (not React), use this approach.

---

## 📦 What You Have in R2

- **20,853 Pokémon card images** (3.37 GB)
- **All properly indexed** with card IDs
- **URL-encoded paths** ready to use
- **1-year CDN cache**

---

## 🎯 Minimal Integration (Copy-Paste)

### Step 1: Add R2 Filename Map

Create `js/r2-cards.js` in your HTML project:

```javascript
// js/r2-cards.js
// Auto-generated R2 card mapping
// Copy contents from ~/Documents/r2FilenameMap.ts 
// Just remove TypeScript syntax

export const r2FilenameMap = {
  "sv3-5-001": "Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_001_std.jpg",
  "sv3-5-002": "Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_002_std.jpg",
  "sv3-5-003": "Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_003_std.jpg",
  // ... 13,605 more entries ...
};

export function getR2ImageUrl(cardId) {
  const filename = r2FilenameMap[cardId];
  if (!filename) return null;
  return `https://pokemontcg.r2.cloudflarestorage.com/${filename}`;
}
```

### Step 2: Use in HTML

```html
<!DOCTYPE html>
<html>
<head>
  <title>Pokémon TCG Marketplace</title>
  <style>
    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 1rem;
      padding: 2rem;
    }
    .card {
      cursor: pointer;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      transition: transform 0.2s;
    }
    .card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .card img {
      width: 100%;
      height: auto;
      display: block;
    }
  </style>
</head>
<body>
  <h1>Pokémon Cards from R2</h1>
  <div class="card-grid" id="cardGrid"></div>

  <script type="module">
    import { getR2ImageUrl } from './js/r2-cards.js';

    // Sample card IDs
    const cards = [
      { id: 'sv3-5-001', name: 'Card 001' },
      { id: 'sv3-5-002', name: 'Card 002' },
      { id: 'xy2-055', name: 'XY2-055' },
      { id: 'me4-001', name: 'Chaos Rising' },
    ];

    const grid = document.getElementById('cardGrid');

    cards.forEach(card => {
      const url = getR2ImageUrl(card.id);
      if (url) {
        const div = document.createElement('div');
        div.className = 'card';
        div.innerHTML = `
          <img src="${url}" alt="${card.name}" loading="lazy">
          <p>${card.name}</p>
        `;
        grid.appendChild(div);
      }
    });
  </script>
</body>
</html>
```

---

## 🔌 Simpler Alternative (No Modules)

If your HTML doesn't support ES6 modules:

```html
<script>
  // Inline the mapping (or load from JSON file)
  const R2_CARDS = {
    "sv3-5-001": "Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_001_std.jpg",
    "sv3-5-002": "Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_002_std.jpg",
    // ... more cards ...
  };

  function getR2ImageUrl(cardId) {
    const filename = R2_CARDS[cardId];
    if (!filename) return null;
    return `https://pokemontcg.r2.cloudflarestorage.com/${filename}`;
  }

  // Use it
  function displayCard(cardId) {
    const url = getR2ImageUrl(cardId);
    if (url) {
      const img = document.createElement('img');
      img.src = url;
      img.alt = cardId;
      document.body.appendChild(img);
    }
  }

  // Example
  displayCard('sv3-5-001');
</script>
```

---

## 📊 Generate JSON Version

If you prefer JSON instead of JavaScript:

```bash
# Convert r2FilenameMap.ts to JSON
cat ~/Documents/r2FilenameMap.ts | sed 's/export const r2FilenameMap: Record<string, string> = //g; s/;//g' > cards.json

# Load in HTML
<script>
  async function loadCards() {
    const response = await fetch('cards.json');
    const R2_CARDS = await response.json();
    // Use it...
  }
  loadCards();
</script>
```

---

## 🎨 Complete Example with Card Grid

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pokémon TCG Marketplace</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 2rem;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
    }

    h1 {
      color: white;
      text-align: center;
      margin-bottom: 2rem;
      font-size: 2.5rem;
    }

    .stats {
      background: white;
      padding: 1rem;
      border-radius: 8px;
      margin-bottom: 2rem;
      text-align: center;
      color: #667eea;
      font-weight: bold;
    }

    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 1.5rem;
    }

    .card {
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      transition: all 0.3s ease;
      cursor: pointer;
    }

    .card:hover {
      transform: translateY(-8px);
      box-shadow: 0 12px 24px rgba(0,0,0,0.2);
    }

    .card-image {
      width: 100%;
      aspect-ratio: 3 / 4;
      object-fit: cover;
      background: #f0f0f0;
    }

    .card-info {
      padding: 1rem;
      text-align: center;
    }

    .card-name {
      font-weight: 600;
      color: #333;
      margin-bottom: 0.25rem;
    }

    .card-set {
      font-size: 0.85rem;
      color: #999;
    }

    .loading {
      text-align: center;
      color: white;
      font-size: 1.2rem;
    }

    .error {
      background: #ff6b6b;
      color: white;
      padding: 1rem;
      border-radius: 8px;
      margin-bottom: 1rem;
    }

    @media (max-width: 768px) {
      .card-grid {
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 1rem;
      }

      h1 {
        font-size: 1.8rem;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>⚡ Pokémon TCG Marketplace</h1>
    <div class="stats">
      ✅ <span id="cardCount">0</span> cards loaded from R2
    </div>
    <div class="card-grid" id="cardGrid"></div>
  </div>

  <script>
    // R2 Configuration
    const R2_BUCKET_URL = 'https://pokemontcg.r2.cloudflarestorage.com';
    
    // Sample card mapping (excerpt from full mapping)
    // In production, load full r2FilenameMap from file
    const R2_CARDS = {
      "sv3-5-001": "Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_001_std.jpg",
      "sv3-5-002": "Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_002_std.jpg",
      "sv3-5-003": "Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_003_std.jpg",
      "sv3-5-004": "Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_004_std.jpg",
      "sv3-5-005": "Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_005_std.jpg",
      "xy2-055": "Pokemon%20TCG/Pokemon%20TCG/base/en_US-XY2-055-skuntank.jpg",
      "me4-001": "chaos-rising/chaos-rising/me4_en_001_std.jpg",
      "swsh1-001": "Pokemon%20TCG/Pokemon%20TCG/sword-shield-base/swsh1_en_001_std.jpg",
    };

    function getR2ImageUrl(cardId) {
      const filename = R2_CARDS[cardId];
      if (!filename) return null;
      return `${R2_BUCKET_URL}/${filename}`;
    }

    function createCardElement(cardId, name, setCode) {
      const url = getR2ImageUrl(cardId);
      if (!url) return null;

      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <img src="${url}" alt="${name}" class="card-image" loading="lazy">
        <div class="card-info">
          <div class="card-name">${name}</div>
          <div class="card-set">${setCode}</div>
        </div>
      `;

      // Click handler (optional)
      card.addEventListener('click', () => {
        console.log('Card clicked:', cardId);
        // Show details, add to cart, etc.
      });

      return card;
    }

    function loadCards() {
      const grid = document.getElementById('cardGrid');
      const counter = document.getElementById('cardCount');

      // Sample cards to display
      const cardsToShow = [
        { id: 'sv3-5-001', name: 'Scarlet Card 1', set: 'SV3.5' },
        { id: 'sv3-5-002', name: 'Scarlet Card 2', set: 'SV3.5' },
        { id: 'sv3-5-003', name: 'Scarlet Card 3', set: 'SV3.5' },
        { id: 'sv3-5-004', name: 'Scarlet Card 4', set: 'SV3.5' },
        { id: 'sv3-5-005', name: 'Scarlet Card 5', set: 'SV3.5' },
        { id: 'xy2-055', name: 'XY2 Card', set: 'XY2' },
        { id: 'me4-001', name: 'Chaos Rising', set: 'ME4' },
        { id: 'swsh1-001', name: 'Sword & Shield', set: 'SWSH1' },
      ];

      let loaded = 0;
      cardsToShow.forEach(card => {
        const element = createCardElement(card.id, card.name, card.set);
        if (element) {
          grid.appendChild(element);
          loaded++;
        }
      });

      counter.textContent = loaded;
    }

    // Load on page load
    document.addEventListener('DOMContentLoaded', loadCards);
  </script>
</body>
</html>
```

---

## 🚀 Steps to Implement

1. **Copy the full r2FilenameMap.ts** from `~/Documents/`
2. **Convert to JavaScript** (remove TypeScript syntax)
3. **Create `js/r2-cards.js`** with the mapping
4. **Add script tag** to your HTML
5. **Use `getR2ImageUrl(cardId)`** anywhere you need images

---

## 🔄 Load All 13,605 Cards

To load the complete mapping:

```javascript
// Option 1: Load as ES6 module
import { r2FilenameMap } from './js/r2-cards-full.js';

// Option 2: Fetch as JSON
async function loadAllCards() {
  const response = await fetch('r2-cards.json');
  const R2_CARDS = await response.json();
  console.log(`Loaded ${Object.keys(R2_CARDS).length} cards`);
}
```

---

## ✅ What's Ready

| File | Purpose |
|------|---------|
| `~/Documents/r2FilenameMap.ts` | Complete 13,605 card mapping |
| `~/Documents/R2_IMAGES_READY.md` | Usage guide |
| Above code examples | Copy-paste ready |

---

**Your images are live in R2. Choose the integration approach that fits your HTML setup!** 🚀
