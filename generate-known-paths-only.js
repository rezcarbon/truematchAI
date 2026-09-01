#!/usr/bin/env node

/**
 * Generate R2 mapping using ONLY confirmed directories
 * We know these exist from our R2 bucket screenshots
 */

const fs = require('fs');
const os = require('os');

function expandUser(filepath) {
  return filepath.replace('~', os.homedir());
}

// ONLY directories we CONFIRMED exist in R2 bucket
const confirmedPaths = {
  // Root level sets (confirmed from screenshots)
  'me2-5': 'ascended-heroes',
  'me3': 'perfect-order',
  'me4': 'chaos-rising',

  // Pokemon TCG subfolder sets (confirmed from screenshots)
  '151': 'Pokemon%20TCG/Pokemon%20TCG/151',
  'xy7': 'Pokemon%20TCG/Pokemon%20TCG/ancient-origins',
  'aquapolis': 'Pokemon%20TCG/Pokemon%20TCG/aquapolis',
  'arceus': 'Pokemon%20TCG/Pokemon%20TCG/arceus',
  'astral-radiance': 'Pokemon%20TCG/Pokemon%20TCG/astral-radiance',
  'base-set': 'Pokemon%20TCG/Pokemon%20TCG/base-set',
  'base-set-2': 'Pokemon%20TCG/Pokemon%20TCG/base-set-2',
  'battle-styles': 'Pokemon%20TCG/Pokemon%20TCG/battle-styles',
  'best-of-game': 'Pokemon%20TCG/Pokemon%20TCG/best-of-game',
  'black-bolt': 'Pokemon%20TCG/Pokemon%20TCG/black-bolt',
};

function generateHTML() {
  console.log(' Generating R2 mapping with CONFIRMED paths only...\n');

  const htmlPath = expandUser('~/Documents/pokemon-r2-smart.html');
  let htmlContent = fs.readFileSync(htmlPath, 'utf8');

  // Build r2SetPaths
  const sortedSets = Object.keys(confirmedPaths).sort();
  const r2SetPathsCode = `const r2SetPaths = {
${sortedSets.map(code => `      "${code}": "${confirmedPaths[code]}",`).join('\n')}
    };`;

  // Replace in HTML
  const oldPattern = /const r2SetPaths = \{[\s\S]*?\};/;
  htmlContent = htmlContent.replace(oldPattern, r2SetPathsCode);

  fs.writeFileSync(htmlPath, htmlContent);

  console.log(` Updated ${htmlPath}\n`);

  // Save reference
  const jsonFile = expandUser('~/Documents/r2-confirmed-paths.json');
  fs.writeFileSync(jsonFile, JSON.stringify(confirmedPaths, null, 2));

  console.log(` Confirmed Sets:\n`);
  console.log(`   Root level: ${Object.keys(confirmedPaths).filter(k => !confirmedPaths[k].includes('Pokemon%20TCG')).length} sets`);
  console.log(`   Pokemon TCG subfolder: ${Object.keys(confirmedPaths).filter(k => confirmedPaths[k].includes('Pokemon%20TCG')).length} sets`);
  console.log(`   Total: ${Object.keys(confirmedPaths).length} sets\n`);

  console.log(`️  NOTE: Only these confirmed paths are included.`);
  console.log(`   Your R2 bucket has 20,853 files total.`);
  console.log(`   To map all files, we need to scan the bucket directly.`);
}

generateHTML();
