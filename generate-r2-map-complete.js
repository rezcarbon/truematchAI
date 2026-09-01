#!/usr/bin/env node

/**
 * Complete r2FilenameMap generator
 * Handles both filename patterns and URL encoding
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

function expandUser(p) {
  if (p.startsWith('~')) {
    return path.join(os.homedir(), p.slice(1));
  }
  return p;
}

const ARCHIVE_PATH = expandUser('~/Downloads/archive');

function extractCardId(filename) {
  // Pattern 1: {setCode}_en_{cardNumber}_std.{ext}
  // Examples: me4_en_117_std.jpg -> me4-117
  //           sv3-5_en_001_std.jpg -> sv3-5-001
  let match = filename.match(/^([a-z0-9\-]+)_en_(\d+)_std/i);
  if (match) {
    return `${match[1]}-${match[2]}`.toLowerCase();
  }

  // Pattern 2: en_US-{setCode}-{cardNumber}-{pokemonName}.jpg
  // Examples: en_US-XY2-055-skuntank.jpg -> xy2-055
  match = filename.match(/^en_US-([A-Za-z0-9]+)-(\d+)-/i);
  if (match) {
    return `${match[1]}-${match[2]}`.toLowerCase();
  }

  return null;
}

function encodeR2Key(r2Key) {
  // URL encode spaces and other special characters
  // R2 stores the actual path, but URLs need encoding
  return r2Key
    .split('/')
    .map(part => encodeURIComponent(part))
    .join('/');
}

function generateMap() {
  const map = {};
  const errors = [];
  let count = 0;
  let skipped = 0;
  const stats = { pattern1: 0, pattern2: 0 };

  function walkDir(dir, relativePath = '') {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        // Skip system files
        if (entry.name.startsWith('.')) continue;

        const fullPath = path.join(dir, entry.name);
        const r2Key = relativePath ? `${relativePath}/${entry.name}` : entry.name;

        if (entry.isDirectory()) {
          walkDir(fullPath, r2Key);
        } else {
          // Extract card ID from filename
          const cardId = extractCardId(entry.name);

          if (cardId) {
            // Store with URL encoding for spaces/special chars
            const encodedR2Key = encodeR2Key(r2Key);
            map[cardId] = encodedR2Key;
            count++;

            // Detect which pattern matched
            if (entry.name.includes('_en_')) {
              stats.pattern1++;
            } else if (entry.name.includes('en_US-')) {
              stats.pattern2++;
            }

            // Log first 15 for verification
            if (count <= 15) {
              console.log(`   "${cardId}" → "${encodedR2Key}"`);
            }
          } else {
            skipped++;
          }
        }
      }
    } catch (err) {
      errors.push(`Error reading ${dir}: ${err.message}`);
    }
  }

  console.log(' Scanning archive for all R2 filenames...\n');
  walkDir(ARCHIVE_PATH);

  console.log(`\n Generated mapping:`);
  console.log(`    Total mapped: ${count} files`);
  console.log(`    Pattern 1 ({setCode}_en_{number}_std.jpg): ${stats.pattern1}`);
  console.log(`    Pattern 2 (en_US-{setCode}-{number}-{name}.jpg): ${stats.pattern2}`);
  console.log(`   ⏭️  Skipped: ${skipped} files (no valid card ID)`);

  if (errors.length > 0) {
    console.log(`   ️  Errors: ${errors.length}`);
  }

  // Get unique set codes
  const setCodes = new Set();
  Object.keys(map).forEach(cardId => {
    const setCode = cardId.split('-')[0];
    setCodes.add(setCode);
  });

  console.log(`\n️  Set codes found: ${Array.from(setCodes).sort().join(', ')}`);
  console.log(`   Total unique sets: ${setCodes.size}`);

  // Generate TypeScript export
  const output = `// Auto-generated R2 filename map with URL encoding
// Generated: ${new Date().toISOString()}
// Total mapped cards: ${count}
//
// Card ID format: {setCode}-{cardNumber}
// Examples:
//   me4-001 = Chaos Rising Set, Card 001
//   sv3-5-042 = Scarlet & Violet 3.5 Set, Card 042
//   xy2-055 = XY2 Set, Card 055
//
// Filenames are URL-encoded (spaces as %20, etc.)
// Ready to use directly in image URLs

export const r2FilenameMap: Record<string, string> = ${JSON.stringify(map, null, 2)};

// Unique set codes in this map
export const R2_SET_CODES = ${JSON.stringify(Array.from(setCodes).sort())};

// Get image URL from card ID
export function getR2ImageUrl(cardId: string): string | null {
  const filename = r2FilenameMap[cardId];
  if (!filename) return null;
  return \`https://pokemontcg.r2.cloudflarestorage.com/\${filename}\`;
}

// Usage:
//
// // Get URL for a specific card
// // Returns: https://pokemontcg.r2.cloudflarestorage.com/chaos-rising/chaos-rising/me4_en_001_std.jpg
//
// // Or use the map directly
// }
`;

  // Write to file
  const outputPath = path.join(expandUser('~/Documents'), 'r2FilenameMap.ts');
  fs.writeFileSync(outputPath, output);

  console.log(`\n Map written to: ${outputPath}`);
  console.log(`\n Sample entries (with URL encoding):`);

  let shown = 0;
  for (const [cardId, r2Key] of Object.entries(map).slice(0, 8)) {
    console.log(`   "${cardId}"`);
    console.log(`   → "${r2Key}"`);
    shown++;
  }

  if (count > 8) {
    console.log(`   ... and ${count - 8} more`);
  }

  console.log(`\n Test one file from R2:`);
  const firstEntry = Object.entries(map)[0];
  if (firstEntry) {
    const [cardId, encodedKey] = firstEntry;
    console.log(`   Card ID: "${cardId}"`);
    console.log(`   R2 URL: https://pokemontcg.r2.cloudflarestorage.com/${encodedKey}`);
    console.log(`   \n   curl -I "https://pokemontcg.r2.cloudflarestorage.com/${encodedKey}"`);
    console.log(`   Should return: HTTP 200 OK`);
  }

  return map;
}

generateMap();
