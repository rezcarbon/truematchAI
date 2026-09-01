# Quick Start: Upload to Cloudflare R2

**Status:** ✅ Ready to upload 3.4GB Pokémon dataset  
**Dataset:** 20,865 files in `/Downloads/archive`  
**Bucket:** pokemontcg (already created on Cloudflare)

---

## 🏃 QUICK START (5 minutes)

### Step 1: Get Credentials
```
1. Go to: https://dash.cloudflare.com
2. Storage & databases → R2 → pokemontcg
3. Copy "Account ID" from the page
4. Go to: Account → API Tokens → R2
5. Create new token with Object Read/Write
6. Copy: Access Key ID & Secret Access Key
```

### Step 2: Set Environment Variables
```bash
bash ~/Documents/setup-r2-env.sh
# Follow the prompts and enter your credentials
```

### Step 3: Verify Setup
```bash
wrangler r2 bucket list
# Should show: pokemontcg ✅
```

### Step 4: Upload
```bash
node ~/Documents/parallel-upload-r2.js
# Wait 5-10 minutes for 3.4GB to upload
```

### Step 5: Verify Success
```bash
wrangler r2 object list pokemontcg | wc -l
# Should show: ~20,865 files ✅
```

---

## 📂 FILES READY IN ~/Documents/

| File | Purpose |
|------|---------|
| `setup-r2-env.sh` | Interactive setup for credentials |
| `parallel-upload-r2.js` | Fast upload (10 concurrent) - **USE THIS** |
| `upload-to-r2.js` | Alternative sequential upload |
| `COMPLETE_R2_UPLOAD_INSTRUCTIONS.md` | Detailed guide (if needed) |
| `WRANGLER_SETUP_GUIDE.md` | Alternative instructions |

---

## ⚡ UPLOAD PERFORMANCE

| Method | Files/sec | Est. Time |
|--------|-----------|-----------|
| Parallel (10) | 80-100 | 5-10 min |
| Sequential | 8-10 | 30-40 min |

**Recommendation:** Use `parallel-upload-r2.js` for fastest upload

---

## 📊 DATASET INFO

```
Location:  ~/Downloads/archive
Files:     20,865
Total Size: 3.4 GB
Structure:
  ├── Pokemon TCG/
  ├── ascended-heroes/
  ├── chaos-rising/
  └── perfect-order/
```

---

## 🎯 EXPECTED OUTPUT

```
🚀 Starting PARALLEL Pokémon TCG Dataset Upload...
📦 Dataset: /Users/modvader/Downloads/archive
🪣 Bucket: pokemontcg
⚡ Concurrent uploads: 10

📊 Scanning files...
✅ Found 20,865 files
✅ Total size: 3.4 GB

⏳ Uploading with 10 concurrent connections...

[25%] 5,216 uploaded, 0 failed - 450 files/min
[50%] 10,432 uploaded, 0 failed - 450 files/min
[75%] 15,648 uploaded, 0 failed - 450 files/min
[100%] 20,865 uploaded, 0 failed - 450 files/min

======================================================================
✅ UPLOAD COMPLETE
======================================================================
✓ Uploaded: 20,865 files
✗ Failed: 0 files
⏱️ Total time: 8 minutes 32 seconds
📊 Total data: 3.4 GB
⚡ Average speed: 400 MB/min
======================================================================

🎉 All files uploaded successfully!

📍 Access your files at:
   https://pokemontcg.r2.cloudflarestorage.com/
```

---

## 🔍 VERIFY AFTER UPLOAD

```bash
# Method 1: Wrangler CLI
wrangler r2 object list pokemontcg | head -10

# Method 2: Direct HTTPS
curl -I https://pokemontcg.r2.cloudflarestorage.com/Pokemon\ TCG/Charizard.png

# Method 3: Cloudflare Dashboard
# https://dash.cloudflare.com → Storage & databases → R2 → pokemontcg
```

---

## 💰 COST

- **Upload:** ~$0.50 (one-time)
- **Storage:** $0.015/GB/month = $0.05/month
- **Egress:** $0 (free via Cloudflare CDN)
- **Total:** ~$1-5/month

---

## ⚠️ TROUBLESHOOTING

**"Command not found: wrangler"**
```bash
npm install -g wrangler
```

**"Missing environment variables"**
```bash
# Check
echo $CLOUDFLARE_ACCOUNT_ID

# If empty, re-run setup
bash ~/Documents/setup-r2-env.sh
```

**"Upload fails"**
```bash
# Just re-run - it continues from where it stopped
node ~/Documents/parallel-upload-r2.js
```

---

## 📱 NEXT STEPS AFTER UPLOAD

1. **Use in React App**
   ```typescript
   const imageUrl = `https://pokemontcg.r2.cloudflarestorage.com/${cardId}.png`;
   <img src={imageUrl} />
   ```

2. **Configure Custom Domain** (Optional)
   ```
   Add CNAME: pokemon-cdn.yourdomain.com → pokemontcg.r2.cloudflarestorage.com
   ```

3. **Start Using in Prototype**
   - Implement `useCardImage` hook
   - Add `CardImage` component
   - Update `CardGrid` to use CDN

---

## 🆘 NEED HELP?

**Full instructions:** `cat ~/Documents/COMPLETE_R2_UPLOAD_INSTRUCTIONS.md`

**Setup help:** `bash ~/Documents/setup-r2-env.sh`

---

## ✅ QUICK CHECKLIST

- [ ] Got R2 API credentials from Cloudflare
- [ ] Ran `bash ~/Documents/setup-r2-env.sh`
- [ ] Verified with `wrangler r2 bucket list`
- [ ] Ran `node ~/Documents/parallel-upload-r2.js`
- [ ] Waited for upload to complete (~10 min)
- [ ] Verified with `wrangler r2 object list pokemontcg | wc -l`
- [ ] Tested HTTPS access to a file
- [ ] Ready to use in React app! 🎉

---

**Ready? Start with Step 1 above! 🚀**
