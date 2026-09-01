#!/usr/bin/env node

/**
 * Verify R2 URLs and find working card images
 * Tests actual URLs to see which ones load from R2
 */

const R2_BUCKET_URL = 'https://pokemontcg.r2.cloudflarestorage.com';

// Sample URLs from our mapping to test
const testUrls = [
  // Scarlet & Violet 3.5
  `${R2_BUCKET_URL}/Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_001_std.jpg`,
  `${R2_BUCKET_URL}/Pokemon%20TCG/Pokemon%20TCG/151/sv3-5_en_002_std.jpg`,

  // Try without URL encoding (spaces as literal)
  `${R2_BUCKET_URL}/Pokemon TCG/Pokemon TCG/151/sv3-5_en_001_std.jpg`,

  // Chaos Rising
  `${R2_BUCKET_URL}/chaos-rising/chaos-rising/me4_en_001_std.jpg`,

  // Try different path structures
  `${R2_BUCKET_URL}/sv3-5/sv3-5_en_001_std.jpg`,
  `${R2_BUCKET_URL}/151/sv3-5_en_001_std.jpg`,
];

console.log(' Testing R2 URLs...\n');
console.log('R2 Bucket: pokemontcg');
console.log('R2 URL: ' + R2_BUCKET_URL);
console.log('---\n');

// For Node.js environment
if (typeof fetch !== 'undefined') {
  testUrls.forEach(async (url) => {
    try {
      const response = await fetch(url, { method: 'HEAD' });
      const status = response.status === 200 ? ' WORKS' : ` ${response.status}`;
      console.log(`${status} | ${url}`);
    } catch (err) {
      console.log(` ERROR | ${url} | ${err.message}`);
    }
  });
}

// Browser-compatible version
if (typeof window !== 'undefined') {
  console.log(' Browser Verification Script');
  console.log('Copy the test URLs below into browser console:\n');

  testUrls.forEach(url => {
    console.log(`fetch('${url}', {method: 'HEAD'}).then(r => console.log('${url} ->',r.status))`);
  });
}

// Better approach: Use the actual mapping
console.log('\n Mapping Verification Steps:');
console.log('1. Open DevTools (F12)');
console.log('2. Go to Network tab');
console.log('3. Load a card from R2');
console.log('4. Look at the actual URL in Network tab');
console.log('5. Compare with our mapping\n');

console.log(' Common Issues:');
console.log('- Spaces might need to be %20 or kept as-is');
console.log('- Directory structure might be different');
console.log('- File extensions might vary (.jpg vs .png)');
console.log('- Path separators might need escaping\n');

console.log(' Solution:');
console.log('Use the working URL format from DevTools Network tab to regenerate mapping.');
