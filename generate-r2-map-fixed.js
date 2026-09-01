#!/usr/bin/env node

/**
 * Generate corrected r2FilenameMap with proper card ID extraction
 * Parses actual R2 filenames from the archive
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
  // Pattern: {setCode}_en_{cardNumber}_std.{ext}
  // Examples: me4_en_117_std.jpg -> me4-117
  //           sv3-5_en_001_std.jpg -> sv3-5-001

  const match = filename.match(/^([a-z0-9\-]+)_en_(\d+)_std/i);
  if (match) {
    return `${match[1]}-${match[2]}`.toLowerCase();
  }

  return null;
}

function generateMap() {
  const map = {};
  const errors = [];
  let count = 0;
  let skipped = 0;

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
            map[cardId] = r2Key;
            count++;

            // Log first 10 for verification
            if (count <= 10) {
              console.log(`   "${cardId}" → "${r2Key}"`);
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

  console.log(' Scanning archive for R2 filenames...\n');
  walkDir(ARCHIVE_PATH);

  console.log(`\n Generated mapping:`);
  console.log(`    Mapped: ${count} files`);
  console.log(`   ⏭️  Skipped: ${skipped} files (no valid card ID)`);

  if (errors.length > 0) {
    console.log(`   ️  Errors: ${errors.length}`);
    errors.slice(0, 3).forEach(e => console.log(`      - ${e}`));
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
  const output = `// Auto-generated R2 filename map
// Generated: ${new Date().toISOString()}
// Total mapped cards: ${count}
//
// Card ID format: {setCode}-{cardNumber}
// Examples:
//   me4-001 = Chaos Rising Set, Card 001
//   sv3-5-042 = Scarlet & Violet 3.5 Set, Card 042

export const r2FilenameMap: Record<string, string> = ${JSON.stringify(map, null, 2)};

// Unique set codes in this map
export const R2_SET_CODES = ${JSON.stringify(Array.from(setCodes).sort())};

// Usage:
// }
`;

  // Write to file
  const outputPath = path.join(expandUser('~/Documents'), 'r2FilenameMap.ts');
  fs.writeFileSync(outputPath, output);

  console.log(`\n Map written to: ${outputPath}`);
  console.log(`\n First 10 entries (verify these match R2):`);

  let shown = 0;
  for (const [cardId, r2Key] of Object.entries(map).slice(0, 10)) {
    console.log(`   "${cardId}": "${r2Key}"`);
    shown++;
  }

  if (count > 10) {
    console.log(`   ... and ${count - 10} more`);
  }

  console.log(`\n Test one file in R2:`);
  const firstEntry = Object.entries(map)[0];
  if (firstEntry) {
    const [cardId, r2Key] = firstEntry;
    console.log(`   curl -I "https://pokemontcg.r2.cloudflarestorage.com/${r2Key}"`);
    console.log(`   Should return: HTTP 200 OK`);
  }

  return map;
}

generateMap();
