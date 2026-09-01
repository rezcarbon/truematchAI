# Wrangler CLI Setup & Upload Guide

## Step 1: Authenticate with Cloudflare

```bash
# Authenticate Wrangler with your Cloudflare account
wrangler login

# This opens a browser window to authorize
# After authorization, Wrangler stores credentials locally
```

## Step 2: Verify R2 Bucket Connection

```bash
# List your R2 buckets to confirm setup
wrangler r2 bucket list

# Should show: pokemontcg
```

## Step 3: Run Upload Script

```bash
# Make script executable
chmod +x ~/Documents/upload-to-r2.js

# Run the upload
node ~/Documents/upload-to-r2.js

# Expected output:
# ✅ Found 20,865 files
# ✅ Total size: 3.4 GB
# ⏳ Uploading in batches of 10...
# [100%] Upload complete!
```

## Alternative: Upload Using Wrangler Directly

If you prefer manual control:

```bash
# Upload all files from a directory
wrangler r2 object put pokemon-images --file ~/Downloads/archive --recursive

# Or upload with dry-run first
wrangler r2 object put pokemon-images --file ~/Downloads/archive --recursive --dry-run
```

## Verify Upload Success

```bash
# List files in bucket
wrangler r2 object list pokemontcg --limit 50

# Check specific file
wrangler r2 object head pokemontcg/Pokemon\ TCG/Charizard.png

# Access via CDN
curl -I https://pokemontcg.r2.cloudflarestorage.com/Pokemon\ TCG/Charizard.png
```

## Troubleshooting

**Issue: "Not authenticated"**
```bash
# Re-authenticate
wrangler login

# Or set environment variables
export CLOUDFLARE_API_TOKEN=your-token
export CLOUDFLARE_ACCOUNT_ID=your-account-id
```

**Issue: "Bucket not found"**
```bash
# Verify bucket name matches
wrangler r2 bucket list

# If pokemontcg doesn't exist, create it
wrangler r2 bucket create pokemontcg
```

**Issue: Upload is slow**
- This is normal for 3.4GB
- Wrangler uploads sequentially
- For faster parallel uploads, use AWS SDK (see below)

## Optional: Faster Upload with AWS SDK

```bash
npm install aws-sdk

# Set environment variables
export AWS_ACCESS_KEY_ID=your-r2-access-key
export AWS_SECRET_ACCESS_KEY=your-r2-secret-key
export AWS_REGION=auto
export AWS_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com

# Run parallel upload script
node parallel-upload.js
```

## Monitor Upload Progress

```bash
# Check bucket size
wrangler r2 bucket list

# Count uploaded files
wrangler r2 object list pokemontcg | wc -l

# Monitor in Cloudflare Dashboard
# https://dash.cloudflare.com → Storage & Databases → R2
```

## Cost Estimate

- **Upload:** <$1 (one-time)
- **Storage:** $0.015/GB/month = $0.05/month
- **Egress:** Free (when served via Cloudflare)
- **Total:** ~$1-5 per month

## Next Steps

1. ✅ Authenticate Wrangler
2. ✅ Run upload script
3. ✅ Verify files in R2
4. ✅ Access via CDN URL
5. ✅ Configure domain (optional)
6. ✅ Integrate with React app
