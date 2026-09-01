#!/usr/bin/env node

/**
 * Scan R2 bucket using direct HTTP requests with AWS SigV4 signing
 */

const crypto = require('crypto');
const https = require('https');
const querystring = require('querystring');
const fs = require('fs');
const os = require('os');

const ACCESS_KEY = process.env.CLOUDFLARE_R2_ACCESS_KEY;
const SECRET_KEY = process.env.CLOUDFLARE_R2_SECRET_KEY;
const ACCOUNT_ID = '6180cb04149e6f50799375c02289662a';
const BUCKET = 'pokemontcg';
const REGION = 'auto';

function expandUser(filepath) {
  return filepath.replace('~', os.homedir());
}

// AWS SigV4 signing
function signRequest(method, path, headers) {
  const timestamp = new Date().toISOString().replace(/[:-]|\.\d{3}/g, '');
  const date = timestamp.slice(0, 8);

  const canonicalRequest = [
    method,
    path,
    '',
    Object.entries(headers)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}:${v}`)
      .join('\n') + '\n',
    Object.keys(headers).sort().join(';'),
    crypto.createHash('sha256').update('').digest('hex'),
  ].join('\n');

  const hashedCanonical = crypto.createHash('sha256').update(canonicalRequest).digest('hex');

  const credentialScope = `${date}/${REGION}/s3/aws4_request`;
  const stringToSign = `AWS4-HMAC-SHA256\n${timestamp}\n${credentialScope}\n${hashedCanonical}`;

  const kDate = crypto.createHmac('sha256', `AWS4${SECRET_KEY}`).update(date).digest();
  const kRegion = crypto.createHmac('sha256', kDate).update(REGION).digest();
  const kService = crypto.createHmac('sha256', kRegion).update('s3').digest();
  const kSigning = crypto.createHmac('sha256', kService).update('aws4_request').digest();
  const signature = crypto.createHmac('sha256', kSigning).update(stringToSign).digest('hex');

  const authHeader = `AWS4-HMAC-SHA256 Credential=${ACCESS_KEY}/${credentialScope}, SignedHeaders=${Object.keys(headers).sort().join(';')}, Signature=${signature}`;

  return {
    ...headers,
    'Authorization': authHeader,
    'X-Amz-Date': timestamp,
  };
}

async function listR2Objects(continuationToken = null) {
  return new Promise((resolve, reject) => {
    const host = `${BUCKET}.${ACCOUNT_ID}.r2.cloudflarestorage.com`;
    let path = '/?list-type=2&max-keys=1000';

    if (continuationToken) {
      path += `&continuation-token=${encodeURIComponent(continuationToken)}`;
    }

    const headers = {
      'host': host,
      'x-amz-content-sha256': crypto.createHash('sha256').update('').digest('hex'),
    };

    const signedHeaders = signRequest('GET', path, headers);

    const options = {
      hostname: host,
      path: path,
      method: 'GET',
      headers: signedHeaders,
    };

    https.request(options, (res) => {
      let data = '';

      res.on('data', chunk => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode !== 200) {
          reject(new Error(`HTTP ${res.statusCode}: ${data.slice(0, 200)}`));
          return;
        }

        // Parse XML response
        const nextToken = data.match(/<NextContinuationToken>([^<]+)<\/NextContinuationToken>/);
        const isTruncated = data.includes('<IsTruncated>true</IsTruncated>');

        const contents = [];
        const contentMatches = data.matchAll(/<Contents>[\s\S]*?<Key>([^<]+)<\/Key>[\s\S]*?<\/Contents>/g);

        for (const match of contentMatches) {
          contents.push(match[1]);
        }

        resolve({
          contents,
          nextToken: nextToken ? nextToken[1] : null,
          isTruncated,
        });
      });
    }).on('error', reject).end();
  });
}

async function scanAllObjects() {
  console.log(' Scanning R2 bucket using HTTP API...\n');

  const allObjects = [];
  let continuationToken = null;
  let pageCount = 0;

  try {
    do {
      pageCount++;
      console.log(` Fetching page ${pageCount}...`);

      const result = await listR2Objects(continuationToken);
      allObjects.push(...result.contents);

      console.log(`   Found ${result.contents.length} objects (total: ${allObjects.length})`);

      continuationToken = result.nextToken;

      if (!result.isTruncated || !continuationToken) {
        break;
      }
    } while (continuationToken);

    console.log(`\n Successfully scanned ${allObjects.length} total objects\n`);

    // Extract directory structure and set mappings
    console.log('️  Analyzing directory structure...\n');

    const setMap = {};
    const directoriesFound = new Set();

    allObjects.forEach(key => {
      const parts = key.split('/');

      if (parts.length >= 2) {
        directoriesFound.add(parts[0]);
      }

      // Extract set code from filename: [setcode]_en_[number]_std.jpg
      const filenameMatch = key.match(/([a-z0-9\-]+)_en_\d{3}_std\.jpg$/i);
      if (filenameMatch) {
        const setCode = filenameMatch[1];
        const fullPath = parts.slice(0, -1).join('/');

        if (!setMap[setCode]) {
          setMap[setCode] = fullPath;
        }
      }
    });

    console.log(` Analysis Results:\n`);
    console.log(`   Total directories: ${directoriesFound.size}`);
    console.log(`   Total set codes found: ${Object.keys(setMap).length}`);
    console.log(`   Root directories: ${Array.from(directoriesFound).join(', ')}\n`);

    // Generate r2SetPaths
    console.log(' Generating r2SetPaths mapping...\n');

    const r2SetPaths = {};
    const sortedSets = Object.keys(setMap).sort();

    console.log('// r2SetPaths mapping:');
    sortedSets.forEach(setCode => {
      const fullPath = setMap[setCode];
      r2SetPaths[setCode] = fullPath;
      console.log(`"${setCode}": "${fullPath}",`);
    });

    console.log(`\n Generated mapping for ${Object.keys(r2SetPaths).length} sets\n`);

    // Update HTML
    console.log(' Updating HTML...\n');

    const htmlPath = expandUser('~/Documents/pokemon-r2-smart.html');
    let htmlContent = fs.readFileSync(htmlPath, 'utf8');

    const r2SetPathsCode = `const r2SetPaths = {
${sortedSets.map(code => `      "${code}": "${setMap[code]}",`).join('\n')}
    };`;

    htmlContent = htmlContent.replace(/const r2SetPaths = \{[\s\S]*?\};/, r2SetPathsCode);
    fs.writeFileSync(htmlPath, htmlContent);

    console.log(` Updated ${htmlPath}\n`);

    // Save JSON mapping
    const mappingFile = expandUser('~/Documents/r2-complete-set-paths.json');
    fs.writeFileSync(mappingFile, JSON.stringify(r2SetPaths, null, 2));
    console.log(` Saved to ${mappingFile}\n`);

    console.log(' Complete! Ready to use:');
    console.log(`    ${Object.keys(r2SetPaths).length} card sets mapped`);
    console.log(`    All ${allObjects.length} files indexed`);
    console.log(`    HTML updated automatically\n`);

    console.log(' Refresh your browser to see all cards loading from R2!');

  } catch (error) {
    console.error(' Error:', error.message);
    process.exit(1);
  }
}

scanAllObjects();
