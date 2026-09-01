# Complete R2 Upload Instructions
## Pokémon TCG Dataset - 3.4GB to Cloudflare R2

---

## 📋 CHECKLIST

- [ ] Step 1: Get R2 API Credentials
- [ ] Step 2: Set Environment Variables
- [ ] Step 3: Verify Wrangler Installation
- [ ] Step 4: Test R2 Connection
- [ ] Step 5: Run Upload Script
- [ ] Step 6: Verify Upload Success

---

## ✅ STEP 1: GET R2 API CREDENTIALS

1. **Go to Cloudflare Dashboard**
   - URL: https://dash.cloudflare.com
   - Log in with your account

2. **Navigate to R2**
   - Left sidebar → Storage & databases → R2

3. **Get Account ID**
   - Click on your bucket "pokemontcg"
   - Copy the **Account ID** from the URL or settings
   - Example: `6180cb04149e6f5079937c022896...`

4. **Create API Token**
   - Left sidebar → Account → API Tokens → R2
   - Click "Create API Token"
   - Settings:
     - **Token Name:** "R2 Upload Token"
     - **Permissions:** Object Read/Write
     - **Bucket:** pokemontcg
     - **TTL:** 1 month (or longer)
   - Click "Create Token"

5. **Copy Credentials**
   - Copy and save:
     - `Access Key ID`
     - `Secret Access Key`
     - Keep these safe! ⚠️

---

## 📝 STEP 2: SET ENVIRONMENT VARIABLES

### Option A: Interactive Setup (Recommended)

```bash
# Run this command - it will prompt you
bash ~/Documents/setup-r2-env.sh
```

### Option B: Manual Setup

```bash
# Open your shell profile
nano ~/.zshrc    # If using zsh
# or
nano ~/.bashrc   # If using bash

# Add these lines at the end:
export CLOUDFLARE_ACCOUNT_ID="your-account-id-here"
export CLOUDFLARE_R2_ACCESS_KEY="your-access-key-here"
export CLOUDFLARE_R2_SECRET_KEY="your-secret-key-here"

# Save and exit (Ctrl+X, then Y, then Enter)

# Reload shell
source ~/.zshrc
# or
source ~/.bashrc
```

### Verify Environment Variables

```bash
echo $CLOUDFLARE_ACCOUNT_ID
echo $CLOUDFLARE_R2_ACCESS_KEY
echo $CLOUDFLARE_R2_SECRET_KEY

# Should output your credentials
```

---

## 🔍 STEP 3: VERIFY WRANGLER INSTALLATION

```bash
# Check version
wrangler --version
# Should show: 4.x.x (or higher)

# Check npm is available
npm --version
```

---

## 🧪 STEP 4: TEST R2 CONNECTION

```bash
# List R2 buckets
wrangler r2 bucket list

# Expected output:
# pokemontcg

# If it doesn't work:
# 1. Check environment variables are set
# 2. Verify credentials are correct
# 3. Re-run: source ~/.zshrc
```

---

## 🚀 STEP 5: RUN UPLOAD SCRIPT

### Option A: Sequential Upload (Slower, but simpler)

```bash
# Install dependencies (if not already installed)
npm install -g aws-sdk

# Run the upload
node ~/Documents/upload-to-r2.js

# Expected output:
# 🚀 Starting Pokémon TCG Dataset Upload...
# 📊 Found 20,865 files
# ✅ Total size: 3.4 GB
# ⏳ Uploading in batches...
# [100%] Upload complete!
```

### Option B: Parallel Upload (Faster, recommended)

```bash
# Install dependencies (if not already installed)
npm install aws-sdk

# Make script executable
chmod +x ~/Documents/parallel-upload-r2.js

# Run the upload
node ~/Documents/parallel-upload-r2.js

# Expected output:
# ⚡ Concurrent uploads: 10
# [25%] 5,216 uploaded...
# [50%] 10,432 uploaded...
# [75%] 15,648 uploaded...
# [100%] Upload complete!
#
# ✅ 20,865 files uploaded
# ⏱️ Total time: 45 minutes (approx)
# 📊 Total data: 3.4 GB
```

### Estimated Upload Times

| Method | Speed | Time |
|--------|-------|------|
| Sequential | 8-10 files/sec | ~30-40 min |
| Parallel (10) | 80-100 files/sec | ~5-10 min |
| Wrangler CLI | 5-8 files/sec | ~50-70 min |

---

## ✨ STEP 6: VERIFY UPLOAD SUCCESS

### Check in Cloudflare Dashboard

```
1. Go to https://dash.cloudflare.com
2. Storage & databases → R2 → pokemontcg
3. Should show ~20,865 objects
4. Total size: ~3.4 GB
```

### Verify via Wrangler

```bash
# List files in bucket
wrangler r2 object list pokemontcg --limit 10

# Expected output:
# Pokemon TCG/Blastoise.png
# Pokemon TCG/Bulbasaur.png
# Pokemon TCG/Charizard.png
# ...

# Count total files
wrangler r2 object list pokemontcg | wc -l
# Should show: ~20,865
```

### Test Direct Access

```bash
# Replace with an actual filename from your dataset
curl -I https://pokemontcg.r2.cloudflarestorage.com/Pokemon\ TCG/Charizard.png

# Expected output:
# HTTP/1.1 200 OK
# Content-Length: (file size)
# Cache-Control: public, max-age=31536000
```

---

## 🎯 NEXT STEPS

After upload succeeds:

### 1. Create Image Manifest

```bash
node ~/Documents/generate-manifest.js
```

This creates `manifest.json` with URLs for all images.

### 2. Configure Custom Domain (Optional)

```bash
# Add CNAME to your domain
# pokemon-cdn.yourdomain.com → pokemontcg.r2.cloudflarestorage.com
```

### 3. Update React App

```typescript
// Use CDN URLs in your app
const imageUrl = `https://pokemontcg.r2.cloudflarestorage.com/${cardId}.png`;
```

### 4. Monitor Costs

- Storage: ~$0.05/month
- Egress: Free (via Cloudflare CDN)
- Total: ~$1-5/month

---

## 🆘 TROUBLESHOOTING

### "Command not found: wrangler"

```bash
# Reinstall Wrangler
npm install -g wrangler

# Verify
wrangler --version
```

### "Missing environment variables"

```bash
# Check if set
echo $CLOUDFLARE_ACCOUNT_ID

# If empty, set them:
export CLOUDFLARE_ACCOUNT_ID="your-id"
export CLOUDFLARE_R2_ACCESS_KEY="your-key"
export CLOUDFLARE_R2_SECRET_KEY="your-secret"

# Or add to ~/.zshrc permanently
```

### "Bucket not found"

```bash
# Verify bucket exists
wrangler r2 bucket list

# If pokemontcg not listed, create it
wrangler r2 bucket create pokemontcg
```

### "Upload fails after N files"

```bash
# Retry - the script resumes from where it stopped
node ~/Documents/parallel-upload-r2.js

# It will skip already-uploaded files and continue
```

### "Slow upload speed"

- Normal for large files (>1MB each)
- Network speed is the bottleneck
- Parallel upload (10 concurrent) is the fastest option

---

## 📊 UPLOAD PROGRESS TRACKING

```bash
# Check upload progress in real-time
watch -n 5 'wrangler r2 object list pokemontcg | wc -l'

# Shows updated file count every 5 seconds
# Keep this running in a separate terminal
```

---

## 🎉 SUCCESS INDICATORS

When upload is complete, you should see:

✅ **In Cloudflare Dashboard:**
- pokemontcg bucket
- 20,865 objects
- 3.4 GB total size

✅ **Via Wrangler CLI:**
```bash
$ wrangler r2 object list pokemontcg
Pokemon TCG/Arcanine.png
Pokemon TCG/Articuno.png
...
(20,865 total)
```

✅ **Accessible via HTTPS:**
```bash
curl -I https://pokemontcg.r2.cloudflarestorage.com/Pokemon\ TCG/Charizard.png
# HTTP/1.1 200 OK
```

---

## 🚀 READY?

1. Get your R2 API credentials (from Cloudflare dashboard)
2. Set environment variables (see Step 2 above)
3. Run: `node ~/Documents/parallel-upload-r2.js`
4. Wait 5-10 minutes ⏳
5. Verify in dashboard ✅
6. Images ready for React app! 🎊

**Any issues?** Check the troubleshooting section above.
