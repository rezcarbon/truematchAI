#!/usr/bin/env node

/**
 * Auto-scan R2 bucket to discover all files and generate complete card mapping
 * Uses AWS SDK v3 for better compatibility
 */

const {
  S3Client,
  ListObjectsV2Command,
} = require('@aws-sdk/client-s3');
const fs = require('fs');
const os = require('os');

function expandUser(filepath) {
  return filepath.replace('~', os.homedir());
}

const ACCESS_KEY = process.env.CLOUDFLARE_R2_ACCESS_KEY || 'bb46301b53003d23b006b7a55b855d6a';
const SECRET_KEY = process.env.CLOUDFLARE_R2_SECRET_KEY || 'dca06dae0170fcf7d3eb916a45166e47ac2551a849f3c9e84d4aa7f357952ec4';
const ACCOUNT_ID = '6180cb04149e6f50799375c02289662a';

async function scanR2Bucket() {
  console.log(' Initializing R2 bucket scan...\n');

  const client = new S3Client({
    region: 'auto',
    credentials: {
      accessKeyId: ACCESS_KEY,
      secretAccessKey: SECRET_KEY,
    },
    endpoint: `https://${ACCOUNT_ID}.r2.cloudflarestorage.com`,
  });

  try {
    console.log(' Connecting to R2 bucket...\n');

    const allObjects = [];
    let continuationToken = null;
    let pageCount = 0;

    // Paginate through all objects
    do {
      pageCount++;
      console.log(` Fetching page ${pageCount}...`);

      const command = new ListObjectsV2Command({
        Bucket: 'pokemontcg',
        MaxKeys: 1000,
        ContinuationToken: continuationToken,
      });

      const response = await client.send(command);

      if (response.Contents) {
        allObjects.push(...response.Contents);
        console.log(`    Found ${response.Contents.length} objects (total: ${allObjects.length})`);
      }

      continuationToken = response.NextContinuationToken;
    } while (continuationToken);

    console.log(`\n Successfully scanned ${allObjects.length} total objects\n`);

    // Parse the structure
    console.log('️  Analyzing structure and extracting card IDs...\n');

    const cardMappings = {}; // cardId → { path, filename }
    const filesByExtension = {};

    allObjects.forEach(obj => {
      const key = obj.Key;
      const parts = key.split('/');
      const filename = parts[parts.length - 1];
      const dir = parts.slice(0, -1).join('/');

      // Track file extensions
      const ext = filename.split('.').pop();
      filesByExtension[ext] = (filesByExtension[ext] || 0) + 1;

      // Try to extract card ID from filename
      // Patterns:
      // 1. [setcode]_en_[number]_std.jpg
      // 2. en_US-[SETCODE]-[number]-[name].jpg
      // 3. [setcode]_en_[number].jpg

      let cardId = null;
      let pattern = null;

      // Pattern 1: setcode_en_number_std.jpg
      const match1 = filename.match(/^([a-z0-9\-]+)_en_(\d{3})_std\.jpg$/i);
      if (match1) {
        cardId = `${match1[1]}-${match1[2]}`;
        pattern = 'std.jpg';
      }

      // Pattern 2: en_US-SETCODE-number-name.jpg
      if (!cardId) {
        const match2 = filename.match(/^en_US-([a-z0-9]+)-(\d{3})-/i);
        if (match2) {
          cardId = `${match2[1].toLowerCase()}-${match2[2]}`;
          pattern = 'en_US-NAME';
        }
      }

      // Pattern 3: setcode_en_number.jpg (no _std)
      if (!cardId) {
        const match3 = filename.match(/^([a-z0-9\-]+)_en_(\d{3})\.jpg$/i);
        if (match3) {
          cardId = `${match3[1]}-${match3[2]}`;
          pattern = 'en.jpg';
        }
      }

      if (cardId && !cardMappings[cardId]) {
        cardMappings[cardId] = {
          path: dir,
          filename: filename,
          pattern: pattern,
        };
      }
    });

    console.log(` Analysis Results:\n`);
    console.log(`   Total files scanned: ${allObjects.length}`);
    console.log(`   Unique card IDs found: ${Object.keys(cardMappings).length}`);
    console.log(`   File types: ${Object.entries(filesByExtension).map(([ext, count]) => `${ext}(${count})`).join(', ')}\n`);

    // Show sample of discovered cards by pattern
    console.log(` Sample discovered cards:\n`);
    const sortedCards = Object.keys(cardMappings).sort();
    sortedCards.slice(0, 30).forEach(cardId => {
      const m = cardMappings[cardId];
      console.log(`   ${cardId}: ${m.filename} (${m.pattern})`);
    });

    if (sortedCards.length > 30) {
      console.log(`   ... and ${sortedCards.length - 30} more cards\n`);
    }

    // Generate the r2ExplicitMappings object
    console.log(`\n Generating complete r2ExplicitMappings...\n`);

    let mappingCode = 'const r2ExplicitMappings = {\n';
    sortedCards.forEach(cardId => {
      const m = cardMappings[cardId];
      mappingCode += `      '${cardId}': {\n`;
      mappingCode += `        path: '${m.path}',\n`;
      mappingCode += `        filename: '${m.filename}'\n`;
      mappingCode += `      },\n`;
    });
    mappingCode += '    };';

    // Update the HTML file
    const htmlPath = expandUser('~/Documents/pokemon-r2-production.html');
    let htmlContent = fs.readFileSync(htmlPath, 'utf8');

    const oldPattern = /const r2ExplicitMappings = \{[\s\S]*?\};/;
    htmlContent = htmlContent.replace(oldPattern, mappingCode);

    fs.writeFileSync(htmlPath, htmlContent);

    console.log(` Updated ${htmlPath}\n`);

    // Save the JSON mapping for reference
    const jsonFile = expandUser('~/Documents/r2-auto-discovered-mapping.json');
    fs.writeFileSync(jsonFile, JSON.stringify(cardMappings, null, 2));
    console.log(` Saved complete mapping to ${jsonFile}\n`);

    // Generate statistics
    const patternStats = {};
    Object.values(cardMappings).forEach(m => {
      patternStats[m.pattern] = (patternStats[m.pattern] || 0) + 1;
    });

    console.log(` Discovered cards by pattern:\n`);
    Object.entries(patternStats)
      .sort((a, b) => b[1] - a[1])
      .forEach(([pattern, count]) => {
        console.log(`   ${pattern}: ${count} cards`);
      });

    console.log(`\n Complete! Generated mapping for ${Object.keys(cardMappings).length} cards\n`);

    console.log(` Files updated:`);
    console.log(`    ${htmlPath}`);
    console.log(`    ${jsonFile}\n`);

    console.log(` Next steps:`);
    console.log(`   1. Refresh your browser to see all ${sortedCards.length} cards!`);
    console.log(`   2. Check console for any cards that still fail to load`);
    console.log(`   3. Deploy pokemon-r2-production.html to production\n`);

    return {
      totalCards: sortedCards.length,
      cardMappings,
      success: true,
    };
  } catch (error) {
    console.error(' Error scanning R2 bucket:');
    console.error(error.message);
    console.error('\n Troubleshooting:');
    console.error('   • Verify credentials are correct');
    console.error('   • Check Account ID matches your Cloudflare account');
    console.error('   • Ensure bucket name is "pokemontcg"');
    console.error('\n Current configuration:');
    console.error(`   Access Key: ${ACCESS_KEY.slice(0, 8)}...`);
    console.error(`   Account ID: ${ACCOUNT_ID}`);
    process.exit(1);
  }
}

// Run the scan
scanR2Bucket().catch(console.error);
