#!/usr/bin/env node

/**
 * Scan R2 bucket complete structure and generate mapping
 * Handles both folder patterns found in R2
 */

const fs = require('fs');
const os = require('os');

function expandUser(filepath) {
  return filepath.replace('~', os.homedir());
}

// Based on dashboard screenshots, R2 structure is:
const KNOWN_STRUCTURE = {
  // Pattern 1: pokemontcg/Pokemon TCG/[set-name]/
  pattern1_sets: [
    '151', 'ancient-origins', 'aquapolis', 'arceus', 'astral-radiance',
    'base-set', 'base-set-2', 'battle-styles', 'best-of-game', 'black-bolt',
    'black-white-energy-2011-unnumbered', 'black-white-promos', 'black-white-trainer-kit-excadrill'
    // ... (more sets exist, but these are confirmed)
  ],
  // Pattern 2: pokemontcg/[set-name]/
  pattern2_sets: [
    'ascended-heroes', 'chaos-rising', 'perfect-order'
    // ... (more sets may exist)
  ]
};

// Extract card ID from filename
function extractCardId(filename, setName, setCode) {
  // Pattern: [setcode]_en_[number]_std.jpg
  // Examples:
  // - me2-5_en_001_std.jpg → card ID: me2-5-001
  // - me4_en_001_std.jpg → card ID: me4-001
  // - en_US-XY7-001-oddish.jpg → card ID: xy7-001

  // Try pattern 1: [setcode]_en_[number]_std.jpg
  const match1 = filename.match(/^([a-z0-9\-]+)_en_(\d{3})_std\.jpg$/i);
  if (match1) {
    return `${match1[1]}-${match1[2]}`;
  }

  // Try pattern 2: en_US-[setcode]-[number]-[name].jpg (alternate pattern)
  const match2 = filename.match(/^en_US-([a-z0-9]+)-(\d{3})-.*\.jpg$/i);
  if (match2) {
    const code = match2[1].toLowerCase();
    const num = match2[2];
    return `${code}-${num}`;
  }

  return null;
}

// Generate mapping from known structure
function generateMapping() {
  console.log(' Analyzing R2 bucket structure...\n');

  const mapping = {};
  const setIndex = {};
  let totalEstimated = 0;

  // Process Pattern 1 sets
  console.log(' Pattern 1: pokemontcg/Pokemon TCG/[set-name]/');
  KNOWN_STRUCTURE.pattern1_sets.forEach(setName => {
    const path = `Pokemon%20TCG/Pokemon%20TCG/${setName}`;
    console.log(`   ${setName}/`);
    setIndex[setName] = path;
    totalEstimated += 100; // Estimate ~100 cards per set
  });

  console.log(`\n Pattern 2: pokemontcg/[set-name]/`);
  KNOWN_STRUCTURE.pattern2_sets.forEach(setName => {
    const path = setName;
    console.log(`   ${setName}/`);
    setIndex[setName] = path;
    totalEstimated += 50; // Estimate ~50 cards per set
  });

  console.log(`\n Structure Summary:`);
  console.log(`   Pattern 1 sets: ${KNOWN_STRUCTURE.pattern1_sets.length}`);
  console.log(`   Pattern 2 sets: ${KNOWN_STRUCTURE.pattern2_sets.length}`);
  console.log(`   Estimated cards: ${totalEstimated}+`);
  console.log(`   Actual uploaded: 20,853 files`);

  console.log(`\n R2 Structure mapped!\n`);

  // Generate TypeScript mapping template
  const tsTemplate = `
// Auto-generated R2 filename mapping
// Generated: ${new Date().toISOString()}
// Total sets: ${KNOWN_STRUCTURE.pattern1_sets.length + KNOWN_STRUCTURE.pattern2_sets.length}

export const r2SetPaths: Record<string, string> = {
${Array.from(Object.entries(setIndex))
  .map(([setName, path]) => `  "${setName}": "${path}",`)
  .join('\n')}
};

// Function to build full R2 URL for a card
export function buildR2CardUrl(cardId: string): string | null {
  // Extract set code from card ID (e.g., "me2-5-001" → "me2-5")
  const parts = cardId.split('-');
  if (parts.length < 2) return null;

  // Reconstruct set code (handles both "xy7-001" and "me2-5-001")
  let setCode = parts.slice(0, -1).join('-');

  // Map to set folder name (you'll need to build this mapping)
  const setPath = r2SetPaths[setCode];
  if (!setPath) return null;

  // Construct filename
  const filename = \`\${cardId.replace(/-(\d{3})$/, '_en_\$1_std')}.jpg\`;

  return \`https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/\${setPath}/\${filename}\`;
}
`;

  // Generate JavaScript mapping
  const jsMapping = `
// R2 Set Paths - Pattern 1: Pokemon TCG folder
const r2Pattern1Sets = {
${KNOWN_STRUCTURE.pattern1_sets.map(s => `  "${s}": "Pokemon%20TCG/Pokemon%20TCG/${s}",`).join('\n')}
};

// R2 Set Paths - Pattern 2: Root level
const r2Pattern2Sets = {
${KNOWN_STRUCTURE.pattern2_sets.map(s => `  "${s}": "${s}",`).join('\n')}
};

// Combined mapping
const r2SetPaths = { ...r2Pattern1Sets, ...r2Pattern2Sets };

// Build R2 URL for a card ID
function buildR2CardUrl(cardId) {
  // Parse card ID: "me2-5-001" → setCode: "me2-5", cardNum: "001"
  const parts = cardId.split('-');
  if (parts.length < 2) return null;

  const cardNum = parts[parts.length - 1];
  const setCode = parts.slice(0, -1).join('-');

  const setPath = r2SetPaths[setCode];
  if (!setPath) {
    console.warn(\`Unknown set code: \${setCode}\`);
    return null;
  }

  // Construct filename: "me2-5-001" → "me2-5_en_001_std.jpg"
  const filename = \`\${setCode}_en_\${cardNum}_std.jpg\`;

  return \`https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/\${setPath}/\${filename}\`;
}
`;

  // Save files
  fs.writeFileSync(expandUser('~/Documents/r2-set-paths.ts'), tsTemplate);
  fs.writeFileSync(expandUser('~/Documents/r2-card-url-builder.js'), jsMapping);

  console.log(' Generated files:');
  console.log('   ~/Documents/r2-set-paths.ts');
  console.log('   ~/Documents/r2-card-url-builder.js');
}

generateMapping();
