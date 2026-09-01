#!/usr/bin/env node

/**
 * Cloudflare R2 Upload Script
 * Uploads Pokémon TCG dataset to R2 with optimization
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const DATASET_PATH = path.expandUser('~/Downloads/archive');
const BUCKET_NAME = 'pokemontcg';
const CONCURRENT_UPLOADS = 5;
const CHUNK_SIZE = 10; // Process 10 files at a time

class R2Uploader {
  constructor(datasetPath, bucketName) {
    this.datasetPath = datasetPath;
    this.bucketName = bucketName;
    this.uploadedCount = 0;
    this.failedCount = 0;
    this.totalFiles = 0;
    this.startTime = Date.now();
  }

  /**
   * Get all files from dataset
   */
  async getAllFiles() {
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
   * Upload a single file using Wrangler
   */
  async uploadFile(localPath, s3Key) {
    try {
      // Determine content type
      const ext = path.extname(localPath).toLowerCase();
      let contentType = 'application/octet-stream';

      if (ext === '.png') contentType = 'image/png';
      else if (ext === '.jpg' || ext === '.jpeg') contentType = 'image/jpeg';
      else if (ext === '.webp') contentType = 'image/webp';
      else if (ext === '.json') contentType = 'application/json';
      else if (ext === '.txt') contentType = 'text/plain';

      // Upload using Wrangler
      const command = `wrangler r2 object put "${s3Key}" --file "${localPath}" --bucket="${this.bucketName}"`;

      execSync(command, { stdio: 'pipe', encoding: 'utf-8' });

      this.uploadedCount++;
      return true;
    } catch (error) {
      console.error(` Failed to upload ${s3Key}: ${error.message}`);
      this.failedCount++;
      return false;
    }
  }

  /**
   * Upload files in batches
   */
  async uploadBatch(files, startIndex, batchSize) {
    const batch = files.slice(startIndex, startIndex + batchSize);

    return Promise.all(
      batch.map(file => this.uploadFile(file.localPath, file.s3Key))
    );
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
    console.log(' Starting Pokémon TCG Dataset Upload to Cloudflare R2');
    console.log(` Dataset: ${this.datasetPath}`);
    console.log(`🪣 Bucket: ${this.bucketName}\n`);

    // Get all files
    console.log(' Scanning files...');
    const files = await this.getAllFiles();
    this.totalFiles = files.length;

    if (this.totalFiles === 0) {
      console.error(' No files found in dataset!');
      process.exit(1);
    }

    // Calculate total size
    const totalSize = files.reduce((sum, f) => sum + f.size, 0);
    console.log(` Found ${this.totalFiles} files`);
    console.log(` Total size: ${this.formatBytes(totalSize)}\n`);

    // Upload in batches
    console.log(`⏳ Uploading in batches of ${CHUNK_SIZE}...\n`);

    for (let i = 0; i < this.totalFiles; i += CHUNK_SIZE) {
      const progress = Math.min(i + CHUNK_SIZE, this.totalFiles);
      const percentage = Math.round((progress / this.totalFiles) * 100);
      const elapsed = this.formatTime(Date.now() - this.startTime);

      console.log(`[${percentage}%] Uploading files ${i + 1}-${progress} of ${this.totalFiles} (${elapsed})`);

      await this.uploadBatch(files, i, CHUNK_SIZE);
    }

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log(' UPLOAD COMPLETE');
    console.log('='.repeat(60));
    console.log(` Uploaded: ${this.uploadedCount} files`);
    console.log(` Failed: ${this.failedCount} files`);
    console.log(`⏱️  Total time: ${this.formatTime(Date.now() - this.startTime)}`);
    console.log(` Total data: ${this.formatBytes(totalSize)}`);
    console.log('='.repeat(60) + '\n');

    if (this.failedCount === 0) {
      console.log(' All files uploaded successfully!');
      console.log(`\n Access your files at:`);
      console.log(`   https://pokemontcg.r2.cloudflarestorage.com/\n`);
    } else {
      console.log(`️  ${this.failedCount} files failed. Please retry.\n`);
    }
  }
}

// Expand ~ in path
path.expandUser = function(p) {
  if (p.startsWith('~')) {
    return path.join(require('os').homedir(), p.slice(1));
  }
  return p;
};

// Run upload
const uploader = new R2Uploader(DATASET_PATH, BUCKET_NAME);
uploader.upload().catch(error => {
  console.error(' Fatal error:', error);
  process.exit(1);
});
