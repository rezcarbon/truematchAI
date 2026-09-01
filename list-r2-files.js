#!/usr/bin/env node

/**
 * List files in R2 bucket to verify actual paths
 * Uses the S3 API endpoint
 */

const AWS = require('aws-sdk');

// R2 Configuration from your bucket settings
const s3 = new AWS.S3({
  accessKeyId: process.env.CLOUDFLARE_R2_ACCESS_KEY,
  secretAccessKey: process.env.CLOUDFLARE_R2_SECRET_KEY,
  endpoint: 'https://6180cb04149e6f50799375c0228962a.r2.cloudflarestorage.com',
  s3ForcePathStyle: true,
  signatureVersion: 'v4',
});

async function listR2Files() {
  try {
    console.log(' Listing files in pokemontcg R2 bucket...\n');

    const params = {
      Bucket: 'pokemontcg',
      MaxKeys: 100, // Start with first 100
    };

    const data = await s3.listObjectsV2(params).promise();

    if (!data.Contents || data.Contents.length === 0) {
      console.log(' No files found in bucket');
      return;
    }

    console.log(` Found ${data.Contents.length} files:\n`);

    // Group by prefix to understand structure
    const prefixes = {};

    data.Contents.forEach(file => {
      const path = file.Key;
      const prefix = path.split('/')[0];

      if (!prefixes[prefix]) {
        prefixes[prefix] = [];
      }
      prefixes[prefix].push(path);

      // Show first 20 files
      if (data.Contents.indexOf(file) < 20) {
        console.log(` ${path}`);
        console.log(`   Size: ${(file.Size / 1024).toFixed(2)} KB`);
        console.log(`   URL: https://pub-480280aafa7ca5d8ade973117a527a1.r2.dev/${encodeURIComponent(path)}\n`);
      }
    });

    console.log(`\n Directory Structure:`);
    Object.entries(prefixes).forEach(([prefix, files]) => {
      console.log(`\n${prefix}/`);
      console.log(`  ${files.length} files`);
      console.log(`  Sample: ${files[0]}`);
    });

    // Show total stats
    if (data.IsTruncated) {
      console.log(`\n️ Bucket has more files (showing first ${data.Contents.length})`);
      console.log(`   Use ContinuationToken to fetch more`);
    }

  } catch (error) {
    console.error(' Error listing R2 bucket:');
    console.error(error.message);
    console.error('\n Make sure environment variables are set:');
    console.error('   CLOUDFLARE_R2_ACCESS_KEY');
    console.error('   CLOUDFLARE_R2_SECRET_KEY');
  }
}

listR2Files();
