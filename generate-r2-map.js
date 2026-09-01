#!/usr/bin/env node

/**
 * Generate r2FilenameMap from the archive directory
 * Maps card IDs to their R2 filenames
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

function generateMap() {
  const map = {};
  const errors = [];
  let count = 0;

  function walkDir(dir, prefix = '') {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        if (entry.name.startsWith('.')) continue;

        const fullPath = path.join(dir, entry.name);
        const r2Key = prefix ? `${prefix}/${entry.name}` : entry.name;

        if (entry.isDirectory()) {
          walkDir(fullPath, r2Key);
        } else {
          // Generate card ID from filename
          const cardId = generateCardId(r2Key);
          if (cardId) {
            map[cardId] = r2Key;
            count++;
          }
        }
      }
    } catch (err) {
      errors.push(`Error reading ${dir}: ${err.message}`);
    }
  }

  function generateCardId(r2Key) {
    // Extract meaningful ID from filename
    // Examples: "Pokemon TCG/Charizard.png" -> "pokemon-tcg-charizard"
    // "Pokemon TCG/151/sv3-5_en_001_std.jpg" -> "sv3-5-001"

    const filename = path.basename(r2Key, path.extname(r2Key));
    const dir = path.dirname(r2Key);

    // Try to extract set code and card number
    const match = filename.match(/([a-z0-9]+)_en_(\d+)/);
    if (match) {
      return `${match[1]}-${match[2]}`.toLowerCase();
    }

    // Fallback: use directory + filename
    return dir === '.'
      ? filename.toLowerCase().replace(/\s+/g, '-')
      : `${dir.replace(/\//g, '-')}-${filename}`.toLowerCase().replace(/\s+/g, '-');
  }

  console.log(' Scanning archive for files...\n');
  walkDir(expandUser(ARCHIVE_PATH));

  console.log(` Generated mapping for ${count} files`);
  if (errors.length > 0) {
    console.log(`️  ${errors.length} errors encountered:\n${errors.join('\n')}`);
  }

  // Generate TypeScript/JavaScript export
  const output = `// Auto-generated R2 filename map
// Generated: ${new Date().toISOString()}
// Total files: ${count}

export const r2FilenameMap = ${JSON.stringify(map, null, 2)};

// Usage:
// } else {
// }
`;

  // Write to file
  const outputPath = path.join(expandUser('~/Documents'), 'r2FilenameMap.ts');
  fs.writeFileSync(outputPath, output);

  console.log(`\n Map written to: ${outputPath}`);
  console.log(`\n Sample entries:`);
  const sampleEntries = Object.entries(map).slice(0, 5);
  sampleEntries.forEach(([id, filename]) => {
    console.log(`   "${id}": "${filename}"`);
  });
  console.log(`   ... and ${count - 5} more`);

  return map;
}

generateMap();
