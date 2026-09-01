#!/usr/bin/env node

/**
 * Scan R2 bucket and generate correct filename mapping
 */

const AWS = require('aws-sdk');
const os = require('os');

function expandUser(filepath) {
  return filepath.replace('~', os.homedir());
}

// R2 Configuration
const s3 = new AWS.S3({
  accessKeyId: process.env.CLOUDFLARE_R2_ACCESS_KEY,
  secretAccessKey: process.env.CLOUDFLARE_R2_SECRET_KEY,
  endpoint: 'https://6180cb04149e6f50799375c0228962a.r2.cloudflarestorage.com',
  s3ForcePathStyle: true,
  signatureVersion: 'v4',
});

async function generateMapping() {
  try {
    console.log(' Scanning R2 bucket to generate correct mapping...\n');

    const allFiles = [];
    let continuationToken = null;
    let pageCount = 0;

    // Paginate through all objects
    do {
      pageCount++;
      console.log(` Scanning page ${pageCount}...`);

      const params = {
        Bucket: 'pokemontcg',
        MaxKeys: 1000,
        ContinuationToken: continuationToken,
      };

      const data = await s3.listObjectsV2(params).promise();

      if (data.Contents) {
        allFiles.push(...data.Contents);
      }

      continuationToken = data.NextContinuationToken;
    } while (continuationToken);

    console.log(`\n Found ${allFiles.length} total files in bucket\n`);

    // Generate mapping from file paths
    const mappings = {};
    const cardIdPattern = /([a-z0-9]+-[a-z0-9]+-\d{3})/i;

    allFiles.forEach(file => {
      const key = file.Key;

      // Extract potential card ID from filename
      const match = key.match(cardIdPattern);
      if (match) {
        const cardId = match[1].toLowerCase();
        // Use the full R2 path with URL encoding
        mappings[cardId] = key;
      }
    });

    console.log(` Generated ${Object.keys(mappings).length} card mappings\n`);

    // Show sample mappings
    console.log('Sample mappings:');
    const sampleKeys = Object.keys(mappings).slice(0, 20);
    sampleKeys.forEach(cardId => {
      const path = mappings[cardId];
      console.log(`  "${cardId}": "${path}",`);
    });

    // Generate TypeScript file
    const tsContent = `// Auto-generated R2 filename mapping from Cloudflare R2 bucket
// Generated: ${new Date().toISOString()}
// Total entries: ${Object.keys(mappings).length}

export const r2FilenameMap: Record<string, string> = {
${Object.entries(mappings)
  .slice(0, 100) // First 100 for file size
  .map(([cardId, path]) => `  "${cardId}": "${path}",`)
  .join('\n')}
  // ... ${Object.keys(mappings).length - 100} more entries
};
`;

    console.log('\n TypeScript mapping file generated!');
    console.log(`   Total cards mapped: ${Object.keys(mappings).length}`);

    // Also generate a JavaScript version for HTML
    const jsContent = `const r2FilenameMap = {
${Object.entries(mappings)
  .map(([cardId, path]) => {
    const encodedPath = path.replace(/ /g, '%20');
    return `  "${cardId}": "${encodedPath}",`;
  })
  .join('\n')}
};`;

    console.log('\n JavaScript mapping generated (ready for HTML)');

    // Save to file
    const fs = require('fs');
    fs.writeFileSync(
      expandUser('~/Documents/r2-complete-mapping.js'),
      jsContent
    );

    console.log('\n Saved to: ~/Documents/r2-complete-mapping.js');

  } catch (error) {
    console.error(' Error scanning R2 bucket:');
    console.error(error.message);
    console.error('\n Make sure environment variables are set:');
    console.error('   CLOUDFLARE_R2_ACCESS_KEY');
    console.error('   CLOUDFLARE_R2_SECRET_KEY');
  }
}

generateMapping();
