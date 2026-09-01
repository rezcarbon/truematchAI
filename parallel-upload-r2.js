#!/usr/bin/env node

/**
 * Parallel Cloudflare R2 Upload Script
 * Faster upload using AWS SDK with concurrent uploads
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const AWS = require('aws-sdk');

// Expand ~ in path
const expandUser = (p) => {
  if (p.startsWith('~')) {
    return path.join(os.homedir(), p.slice(1));
  }
  return p;
};

// Configuration
const DATASET_PATH = expandUser('~/Downloads/archive');
const BUCKET_NAME = 'pokemontcg';
const CONCURRENT_UPLOADS = 10; // Parallel uploads
const CHUNK_SIZE = 100; // Files per batch

// Configure S3 client for R2
const s3 = new AWS.S3({
  accessKeyId: process.env.CLOUDFLARE_R2_ACCESS_KEY,
  secretAccessKey: process.env.CLOUDFLARE_R2_SECRET_KEY,
  endpoint: `https://${process.env.CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com`,
  s3ForcePathStyle: true,
  signatureVersion: 'v4',
  maxRetries: 3
});

class ParallelR2Uploader {
  constructor(datasetPath, bucketName) {
    this.datasetPath = datasetPath;
    this.bucketName = bucketName;
    this.uploadedCount = 0;
    this.failedCount = 0;
    this.totalFiles = 0;
    this.startTime = Date.now();
    this.queue = [];
    this.processing = 0;
  }

  /**
   * Get all files from dataset
   */
  getAllFiles() {
    const files = [];

    const walkDir = (dir, prefix = '') => {
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        // Skip system files
        if (entry.name.startsWith('.')) continue;

        const fullPath = path.join(dir, entry.name);
        const s3Key = prefix ? `${prefix}/${entry.name}` : entry.name;

        if (entry.isDirectory()) {
          walkDir(fullPath, s3Key);
        } else {
          files.push({
            localPath: fullPath,
            s3Key: s3Key,
            size: fs.statSync(fullPath).size
          });
        }
      }
    };

    walkDir(this.datasetPath);
    return files;
  }

  /**
   * Get content type based on file extension
   */
  getContentType(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    const types = {
      '.png': 'image/png',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.webp': 'image/webp',
      '.json': 'application/json',
      '.txt': 'text/plain',
      '.gif': 'image/gif'
    };
    return types[ext] || 'application/octet-stream';
  }

  /**
   * Upload a single file
   */
  async uploadFile(localPath, s3Key) {
    return new Promise((resolve) => {
      const fileContent = fs.readFileSync(localPath);
      const contentType = this.getContentType(localPath);

      s3.putObject({
        Bucket: this.bucketName,
        Key: s3Key,
        Body: fileContent,
        ContentType: contentType,
        CacheControl: 'public, max-age=31536000' // 1 year cache
      }, (err, data) => {
        if (err) {
          console.error(` Failed: ${s3Key} - ${err.message}`);
          this.failedCount++;
        } else {
          this.uploadedCount++;
        }
        resolve();
      });
    });
  }

  /**
   * Process queue with concurrency limit
   */
  async processQueue() {
    if (this.queue.length === 0 || this.processing >= CONCURRENT_UPLOADS) {
      return;
    }

    this.processing++;
    const file = this.queue.shift();

    await this.uploadFile(file.localPath, file.s3Key);

    this.processing--;
    this.processQueue();
  }

  /**
   * Format bytes to readable size
   */
  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Format time elapsed
   */
  formatTime(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  }

  /**
   * Main upload process
   */
  async upload() {
    console.log(' Starting PARALLEL Pokémon TCG Dataset Upload to Cloudflare R2');
    console.log(` Dataset: ${this.datasetPath}`);
    console.log(`🪣 Bucket: ${this.bucketName}`);
    console.log(` Concurrent uploads: ${CONCURRENT_UPLOADS}\n`);

    // Verify credentials
    if (!process.env.CLOUDFLARE_R2_ACCESS_KEY || !process.env.CLOUDFLARE_R2_SECRET_KEY || !process.env.CLOUDFLARE_ACCOUNT_ID) {
      console.error(' Missing environment variables!');
      console.error('Please set:');
      console.error('  CLOUDFLARE_R2_ACCESS_KEY');
      console.error('  CLOUDFLARE_R2_SECRET_KEY');
      console.error('  CLOUDFLARE_ACCOUNT_ID');
      process.exit(1);
    }

    // Get all files
    console.log(' Scanning files...');
    const files = await Promise.resolve(this.getAllFiles());
    this.totalFiles = files.length;
    this.queue = [...files];

    if (this.totalFiles === 0) {
      console.error(' No files found in dataset!');
      process.exit(1);
    }

    // Calculate total size
    const totalSize = files.reduce((sum, f) => sum + f.size, 0);
    console.log(` Found ${this.totalFiles} files`);
    console.log(` Total size: ${this.formatBytes(totalSize)}\n`);

    // Upload with parallel processing
    console.log(`⏳ Uploading with ${CONCURRENT_UPLOADS} concurrent connections...\n`);

    const uploadPromises = [];
    const statusInterval = setInterval(() => {
      const progress = Math.round(((this.uploadedCount + this.failedCount) / this.totalFiles) * 100);
      const elapsed = this.formatTime(Date.now() - this.startTime);
      const rate = Math.round((this.uploadedCount + this.failedCount) / (((Date.now() - this.startTime) / 1000) / 60));

      console.log(
        `[${progress}%] ${this.uploadedCount} uploaded, ${this.failedCount} failed - ${rate} files/min (${elapsed})`
      );
    }, 5000);

    // Start concurrent uploaders
    for (let i = 0; i < CONCURRENT_UPLOADS; i++) {
      uploadPromises.push(this.processUploads());
    }

    await Promise.all(uploadPromises);
    clearInterval(statusInterval);

    // Final summary
    console.log('\n' + '='.repeat(70));
    console.log(' UPLOAD COMPLETE');
    console.log('='.repeat(70));
    console.log(` Uploaded: ${this.uploadedCount} files`);
    console.log(` Failed: ${this.failedCount} files`);
    console.log(`⏱️  Total time: ${this.formatTime(Date.now() - this.startTime)}`);
    console.log(` Total data: ${this.formatBytes(totalSize)}`);
    console.log(` Average speed: ${Math.round(totalSize / 1024 / 1024 / (((Date.now() - this.startTime) / 1000) / 60))} MB/min`);
    console.log('='.repeat(70) + '\n');

    if (this.failedCount === 0) {
      console.log(' All files uploaded successfully!');
      console.log(`\n Access your files at:`);
      console.log(`   https://pokemontcg.r2.cloudflarestorage.com/\n`);
      console.log(` Or with custom domain (if configured):`);
      console.log(`   https://images.pokemon-marketplace.com/\n`);
    } else {
      console.log(`️  ${this.failedCount} files failed.`);
      console.log(`   Retry with: node parallel-upload-r2.js\n`);
    }
  }

  /**
   * Process uploads from queue
   */
  async processUploads() {
    while (this.queue.length > 0) {
      await this.processQueue();
      // Small delay to prevent overwhelming the system
      await new Promise(resolve => setTimeout(resolve, 10));
    }
  }
}

// Run upload
const uploader = new ParallelR2Uploader(DATASET_PATH, BUCKET_NAME);
uploader.upload().catch(error => {
  console.error(' Fatal error:', error);
  process.exit(1);
});
